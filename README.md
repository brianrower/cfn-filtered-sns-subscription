# cfn-filtered-sns-subscription
A CloudFormation custom resource provider for deploying a SNS subscription with a filter

## How do I generate a secret?
It is quite easy: you specify a CloudFormation resource of the [Custom::Secret](docs/Custom%3A%3ASecret.md), as follows:

```json
  "Resources": {
    "SNSSubscription": {
      "Type": "Custom::FilteredSNSSubscription",
      "Properties": {
        "Endpoint": "test@example.com",
        "TopicArn": { "Ref" : "MySNSTopic" },
        "Protocol": "email"
      }
    }
  }
```

## Installation
To install this custom resources, type:

```sh
aws cloudformation create-stack \
	--capabilities CAPABILITY_IAM \
	--stack-name cfn-filtered-sns-subscription-provider \
	--template-body file://cloudformation/cfn-filtered-sns-subscription-provider.json 

aws cloudformation wait stack-create-complete  --stack-name cfn-filtered-sns-subscription-provider
```
