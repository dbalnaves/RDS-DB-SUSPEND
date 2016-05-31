#!/usr/bin/python

import json, sys
import subprocess,os
import jmespath
import urllib2

databases=["data-test"]
bucket="data-db-suspend"
snapshot_suffix="-nightly"
role="DATA-DB-SUSPEND"

bucket_path="s3://"+bucket+"/"

response=urllib2.urlopen("http://169.254.169.254/latest/dynamic/instance-identity/document").read()
document=json.loads(response)
role_arn="arn:aws:iam::"+document["accountId"]+":role/"+role

response=subprocess.check_output(["/usr/bin/aws","sts","assume-role","--role-arn",role_arn,"--role-session-name","DATA-DB-SUSPEND"])

credentials=jmespath.search("Credentials.[AccessKeyId,SecretAccessKey,SessionToken]",json.loads(response))
credentials_env=os.environ
credentials_env["AWS_ACCESS_KEY_ID"]=credentials[0]
credentials_env["AWS_SECRET_ACCESS_KEY"]=credentials[1]
credentials_env["AWS_SECURITY_TOKEN"]=credentials[2]

try:
    process=subprocess.Popen(["/usr/bin/aws","rds","describe-db-instances"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=credentials_env)
    response,error=process.communicate()
except subprocess.CalledProcessError as error:
    print "ERROR: Query RDS instances failed:", error.output
    sys.exit(1)

all_db_meta=json.loads(response)

db_meta_list=[]
for db_name in databases:
    db_meta_list.append(jmespath.search("DBInstances[?DBInstanceIdentifier=='"+db_name+"']",all_db_meta))

if len(db_meta_list):
    try:
        response=subprocess.check_output(["/usr/bin/aws","s3","ls",bucket_path],stderr=subprocess.STDOUT, env=credentials_env)
    except subprocess.CalledProcessError as error:
        if 'NoSuchBucket' in error.output:
            print "ERROR: Bucket \""+bucket+"\" does not exist."
            sys.exit(1)
        
for db_meta in db_meta_list:
    db_meta_path=bucket_path+db_meta[0]["DBInstanceIdentifier"]+snapshot_suffix
    try:
        process=subprocess.Popen(["/usr/bin/aws","s3","cp","-",db_meta_path], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=credentials_env)
        response,error=process.communicate(json.dumps(db_meta))
    except subprocess.CalledProcessError as error:
        print "ERROR: Failed writing db state to \""+db_meta_path+"\":", error.output
        sys.exit(1)

    try:
        process=subprocess.Popen(["/usr/bin/aws","rds","delete-db-instance","--no-skip-final-snapshot","--db-instance-identifier",db_meta[0]["DBInstanceIdentifier"],"--final-db-snapshot-identifier",db_meta[0]["DBInstanceIdentifier"]+snapshot_suffix], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=credentials_env)
        response,error=process.communicate()
    except subprocess.CalledProcessError as error:
        print "ERROR: Failed to terminate db instance \""+db_meta[0]["DBInstanceIdentifier"]+"\":", error.output
        sys.exit(1)

    try:
        process=subprocess.Popen(["/usr/bin/aws","rds","wait","db-instance-deleted","--db-instance-identifier",db_meta[0]["DBInstanceIdentifier"]],env=credentials_env)
        response,error=process.communicate()
    except subprocess.CalledProcessError as error:
        print "ERROR: Failed to enter wait while terminating db instance \""+db_meta[0]["DBInstanceIdentifier"]+"\":", error.output
        sys.exit(1)

print "INFO: Suspend db instane \""+db_meta[0]["DBInstanceIdentifier"]+"\" complete."
sys.exit(0)
