# ai-data-integration

#ai-data-integration-lambda

1. Before pushing the code to the github add the secets and variables in the github repository
   .In Secrets:
   1. AWS_ACCESS_KEY_ID
   2. AWS_SECRET_ACCESS_KEY
      In Variables:
   3. REGION
   4. ROLE (with all the permission enabled)
   5. BUCKET_NAME
   6. ECR_REPOSITORY
2. Then push the code to the github repository
3. The code will automatically uploaded to aws lambda
4. After that in the lambda function in configuration-> variables add the environment variables values that are specified there.
