import boto3
import subprocess
import time
import calendar
import sys
import json
def gethostedzone(domain):
    session = boto3.Session(profile_name='me')
    client = session.client('route53')
    response = client.list_hosted_zones_by_name()
    zoneId = "not found"
    for zone in response.get("HostedZones"):
        currentid = zone.get("Id").strip("/hostedzone/")
        if zone.get("Name") == domain:
            zoneId = currentid
    return zoneId
def getdnsvalue(fqdn, hostedzone):
    session = boto3.Session(profile_name='me')
    client = session.client('route53')
    awsresponse = client.test_dns_answer(HostedZoneId=hostedzone, RecordName=fqdn, RecordType=rectype)
    dnsrecord = ""
    for rec in awsresponse.get("RecordData"):
        dnsrecord = dnsrecord + rec.strip("\"")
    return dnsrecord
def route53update(subdomain, domain, value, rectype, hostedzone, consoleOut=True):
    fqdn = subdomain + "." + domain[:-1]
    session = boto3.Session(profile_name='me')
    client = session.client('route53')
    changes = {
        "Comment": "Adds a dns record for a domain",
        "Changes": [
            {
                "Action": "UPSERT",
                "ResourceRecordSet": {
                "Name": subdomain + "." + domain,
                "Type": rectype,
                "TTL": 0,
                "ResourceRecords": [
                        {
                            "Value": "\"" + value + "\""
                        }
                    ]
                }
            }
        ]
    }
    startTime = calendar.timegm(time.gmtime())
    client.change_resource_record_sets(HostedZoneId=hostedzone, ChangeBatch=changes)
    dnsRecord = getdnsvalue(fqdn, hostedzone)
    while dnsRecord != value:
        if consoleOut:
            print("Current DNS record is " + dnsRecord + " and not " + value + ".\nWaiting 10 seconds and trying again.")
        time.sleep(10)
        now = calendar.timegm(time.gmtime())
        dnsRecord = getdnsvalue(fqdn, hostedzone)
    now = calendar.timegm(time.gmtime())
    timespent = now - startTime
    if consoleOut:
        print("Current DNS record is " + dnsRecord + " and matches " + value + ".\nUpdate took " + str(timespent) + " seconds to complete.")
if __name__ == '__main__':
    try: 
        subdomain = sys.argv[1]
        domain = sys.argv[2]
        value = sys.argv[3]
        rectype = sys.argv[4].upper()
        try:
            zone = sys.argv[5]
        except:
            zone = gethostedzone(domain)
        if zone == "not found":
            print("A zone id for " + domain + " could not be found. If you know it, you can try to submit it manually as the last argument")
        else:
            route53update(subdomain, domain, value, rectype, zone)
    except Exception as e:
        print(e)
        print("Please specific domain, value and rectype to be updated.\nEg: python3 new-dns-entry.py myapp example.com. ilovedns txt (optional zone id)")