#!/usr/bin/python

import json, sys
import subprocess,os
import jmespath
import requests

bucket="data-db-suspend"
snapshot_suffix="-nightly"
role="DATA-DB-SUSPEND"

bucket_path="s3://"+bucket+"/"
response=requests.get("http://169.254.169.254/latest/dynamic/instance-identity/document")
document=json.loads(response)
role_arn="arn:aws:iam::"+document["accountId"]+":role/"+role

response=subprocess.check_output(["/usr/bin/aws","sts","assume-role","--role-arn",role_arn,"--role-session-name","DATA-DB-SUSPEND"])

credentials=jmespath.search("Credentials.[AccessKeyId,SecretAccessKey,SessionToken]",json.loads(response))
credentials_env=os.environ
credentials_env["AWS_ACCESS_KEY_ID"]=credentials[0]
credentials_env["AWS_SECRET_ACCESS_KEY"]=credentials[1]
credentials_env["AWS_SECURITY_TOKEN"]=credentials[2]

try:
    process=subprocess.Popen(["/usr/bin/aws","s3api","list-objects","--bucket",bucket], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=credentials_env)
    response,error=process.communicate()
except subprocess.CalledProcessError as error:
    print "ERROR: Failed to list \""+bucket_path+"\":", error.output
    sys.exit(1)

db_state_list=jmespath.search("Contents[].Key",json.loads(response))
for db_state in db_state_list:
    db_meta_path=bucket_path+db_state
    try:
        process=subprocess.Popen(["/usr/bin/aws","s3","cp",db_meta_path,"-"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=credentials_env)
        response,error=process.communicate()
    except subprocess.CalledProcessError as error:
        print "ERROR: Failed reading db state from \""+db_meta_path+"\":", error.output
        sys.exit(1)

    db_meta=jmespath.search("[0]",json.loads(response))

    try:
        process=subprocess.Popen(["/usr/bin/aws","rds","restore-db-instance-from-db-snapshot","--db-snapshot-identifier",db_state,"--db-instance-identifier",db_meta["DBInstanceIdentifier"]], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=credentials_env)
        response,error=process.communicate()
    except subprocess.CalledProcessError as error:
        print "ERROR: Failed to restore db \""+db_meta["DBInstanceIdentifier"]+"\":", error.output
        sys.exit(1) 

    try:
        process=subprocess.Popen(["/usr/bin/aws","rds","wait","db-instance-available","--db-instance-identifier",db_meta["DBInstanceIdentifier"]], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=credentials_env)
        response,error=process.communicate()
    except subprocess.CalledProcessError as error:
        print "ERROR: Failed to enter wait while creating db instance \""+db_meta["DBInstanceIdentifier"]+"\":", error.output
        sys.exit(1)

    try:
        process=subprocess.Popen(["/usr/bin/aws","rds","delete-db-snapshot","--db-snapshot-identifier",db_state], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=credentials_env)
        response,error=process.communicate()
    except subprocess.CalledProcessError as error:
        print "ERROR: Failed to db state snapshot \""+db_state+"\":", error.output
        sys.exit(1)

    db_meta_path=bucket_path+db_meta["DBInstanceIdentifier"]+snapshot_suffix
    try:
        process=subprocess.Popen(["/usr/bin/aws","s3","rm",db_meta_path,"-"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=credentials_env)
        response,error=process.communicate()
    except subprocess.CalledProcessError as error:
        print "ERROR: Failed to delete db state from \""+db_meta_path+"\":", error.output
        sys.exit(1)

    print "INFO: Restore db instane \""+"DBInstanceIdentifier"+"\" complete."
    sys.exit(0)
