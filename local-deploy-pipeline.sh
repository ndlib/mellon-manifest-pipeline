#
# note this is not a complete script it is missing some requiree parameter overrides
# it is only able to do an update.
# this also requires blueprints
#
templatePath='deploy/cloudformation/manifest-pipeline-pipeline.yml'
templatePath='../mellon-blueprints/deploy/cloudformation/manifest-pipeline-pipeline.yml'

stackName='new-csv'
aws cloudformation deploy \
  --capabilities CAPABILITY_NAMED_IAM \
  --region us-east-1 \
  --stack-name $stackName \
  --template-file $templatePath \
  --parameter-overrides \
      SentryDsn=https://136d489c91484b55be18e0a28d463b43@sentry.io/1831199 \
      RBSCS3ImageBucketName="rbsc-test-files"
