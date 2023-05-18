# cloud_sherlock

# Enum S3 buckets and SaaS

For now cloud_sherlock supports the following services:
- Slack
- Atlassian
- Salesforce
- Scaleway S3
- Exoscale S3
- OVHCloud S3
- Ionos S3
- Linode S3
- Vultr S3
- Digital Ocean S3

Cloud_sherlock can be run in two modes:
- Generate and enum (generate bucketnames for you based on company's name)
- Enum (run enumeration based on submitted namespaces' and buckets' files)

Generate:
```
$ python3 cloud_sherlock.py --generate --name <name> --rps 100
```
Enum with prepared list (your bucketnames file):
```
$ python3 cloud_sherlock.py --buckets <buckets.txt> --name <test> --rps 100
```
To generate mutations with default buckets list
```
$ python3 cloud_sherlock.py --generate --name <name> --rps 100
```
