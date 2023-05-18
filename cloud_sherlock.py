import click
import os
import time
import asyncio
from config import *
import aiohttp

start_time = time.time()
script_path = os.path.dirname(os.path.abspath(__file__))
url_list_results = list()

SAAS_URLS = GL
BUCKET_URLS = EU_BUCKET_URLS

def read_payload_file(file_path: str):
    with open(file_path) as file_obj:
        return (line.strip() for line in file_obj.readlines() if line)

def uniq(func):
    def inner(*args, **kwargs):
        return list(set(func(*args, **kwargs)))
    return inner


@click.command()
@click.option('--name', '-n', help='Enter company\'s name', default='')
@click.option('--generate', help='Let cloud_sherlock generate all for you', type=bool, is_flag=True, default=False)
@click.option('--buckets', type=click.Path(exists=True), help='File with generated bucket names',
              default=os.path.join(script_path, 'bucketnames.txt'))
@click.option('--rps', '-rps', help='Enter number of requests per second to init', type=int, default=100)
def cloud_sherlock(name, generate, buckets, rps):

    bucketnames_data = read_payload_file(buckets)

    if generate:
        mutations = generate_mutations(name, bucketnames_data)
        gen = generate_enum_payload_chunk(saas_payload=mutations,
                              buckets_payload=mutations)
        print_stats(name, buckets, rps, mutations)
    else:
        gen = generate_enum_payload_chunk(saas_payload=[name],
                              buckets_payload=bucketnames_data)
        print_stats(name, buckets, rps, mutations=[])

    

    asyncio.run(brute(gen, rps))

    print(f"Time elapsed: {str(time.time() - start_time)}")
    print(f'Found {len(url_list_results)} results')


def print_stats(name, buckets, rps, mutations):
    print(f"[*] Enumerating for name: {name}")
    print(f"[*] Buckets filename: {buckets}")
    if (mutations):
        print(f"[*] Size of mutations: {len(mutations)}")
    print(f"[*] Requests per second: {rps}")


async def get(client, queue):
    failed_http_codes = [404, 434, 400]
    while True: 
        
        url = await queue.get()
        
        try:
            resp = await client.get(url, allow_redirects=True)
            if resp.status not in failed_http_codes:
                url_list_results.append({'url': url, 'code': resp.status})
                print(f"[+] Found - {url} : {str(resp.status)}")
        except Exception as ex:
            pass
        finally:
            queue.task_done()


@uniq
def generate_mutations(company_name: str, mutation_payload: list[str]) -> list[str]:
    mutations = [company_name]

    for mutation in mutation_payload:
        mutations.append(f"{mutation}-{company_name}")
        mutations.append(f"{company_name}-{mutation}")

    return mutations


def generate_enum_payload_chunk(saas_payload: list[str], buckets_payload: list[str]):
    """
    @param saas_payload: a list of strings for SAAS_URLS
    @param buckets_payload: a list of strings for BUCKET_URLS
    @return:
    """

    _enum_saas = enum_saas(saas_payload)
    for res in _enum_saas:
        yield res
    
    _enum_buckets = enum_buckets(buckets_payload)
    for res in _enum_buckets:
        yield res

def fill_template(template_urls: list[str], mutations: list[str], field_name: str):
    """ Fills template urls.
    @param template_urls: a list of urls
    @param mutations: a list of strings to be substituted in the urls
    @param field_name: a string to be replaced, e.g. `bucketname`
    @return: list of urls with ...
    """

    for tmp_url in template_urls:
        for mutation in mutations:
            yield tmp_url.format(**{field_name: mutation})
    

@uniq
def enum_saas(mutations: list[str]) -> list[str]:
    return fill_template(template_urls=SAAS_URLS, mutations=mutations, field_name='name')


def enum_buckets(mutations: list[str]) -> list[str]:
    return fill_template(template_urls=BUCKET_URLS, mutations=mutations, field_name='bucketname')

async def brute(gen, rps):
    tasks = []
    queue = asyncio.Queue(maxsize=20)
    connector = aiohttp.TCPConnector(limit=rps, ssl=False)
    async with aiohttp.ClientSession(connector=connector) as sess:
        for i in range(10):
            task = asyncio.create_task(get(sess, queue))
            tasks.append(task)

        for url in gen:
            await queue.put(url)
            
        await queue.join()
        
        for task in tasks:
           task.cancel()
        
        await asyncio.gather(*tasks, return_exceptions=True)
        
        await sess.close()

if __name__ == '__main__':
    cloud_sherlock()
