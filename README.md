# RDS-DB-SUSPEND

Role:
```
$ aws iam list-attached-role-policies --role-name data-db-suspend
{
    "AttachedPolicies": [
        {
            "PolicyName": "AmazonRDSFullAccess",
            "PolicyArn": "arn:aws:iam::aws:policy/AmazonRDSFullAccess"
        },
        {
            "PolicyName": "AmazonS3FullAccess",
            "PolicyArn": "arn:aws:iam::aws:policy/AmazonS3FullAccess"
        }
    ]
}
```

Bucket Policy:
```
{
	"Version": "2012-10-17",
	"Statement": [
		{
			"Sid": "",
			"Effect": "Deny",
			"NotPrincipal": {
				"AWS": "arn:aws:iam::6969696969:user/dbalnaves
			},
			"Action": "s3:*",
			"Resource": [
				"arn:aws:s3:::data-db-suspend/*",
				"arn:aws:s3:::data-db-suspend"
			],
			"Condition": {
				"StringNotLike": {
					"aws:userid": "ROLE_ID_HERE:*"
				}
			}
		},
		{
			"Sid": "",
			"Effect": "Deny",
			"Principal": {
				"AWS": "arn:aws:iam::6969696969:role/DATA-DB-SUSPEND"
			},
			"NotAction": [
				"s3:PutObject",
				"s3:GetObject",
				"s3:DeleteObject",
				"s3:ListBucket"
			],
			"Resource": [
				"arn:aws:s3:::data-db-suspend/*",
				"arn:aws:s3:::data-db-suspend"
			]
		},
		{
			"Sid": "",
			"Effect": "Allow",
			"Principal": {
				"AWS": "arn:aws:iam::6969696969:role/DATA-DB-SUSPEND"
			},
			"Action": [
				"s3:PutObject",
				"s3:ListBucket",
				"s3:GetObject",
				"s3:DeleteObject"
			],
			"Resource": [
				"arn:aws:s3:::data-db-suspend/*",
				"arn:aws:s3:::data-db-suspend"
			]
		}
	]
}
```
