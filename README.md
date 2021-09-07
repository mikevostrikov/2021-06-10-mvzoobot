# Toronto Zoo Tickets Availabaility Notifier

This app is aimed to notify (via Telegram) a user when there are weekend mornings tickets available at [Toronto Zoo](https://www.torontozoo.com/).

## About The Project

Toronto Zoo is an amazing place to visit with your family and friends. For many the preferred time to visit the zoo is weekend mornings. That is why the tickets for those times run out fast.
This app checks for the weekend mornings tickets availability every 10 minutes and notifies the user as soon as the tickets become available. The user can react fast and be the first to buy a ticket for the preferred time.

### Design Idea
AWS Lambda function fetches the content from a static URL belonging to the zoo web-site to check for the tickets availability. If there are tickets available for the weekend mornings, the AWS Lambda function sends a message to a specified Telegram chat using Telegram Bot API.
AWS Lambda function is triggered on schedule every 10 minutes with the help of the CloudWatch EventBridge service.

### Built With

* Python 3.8 - serverless app function code
* Telegram - messaging service for notifications delivery
* AWS - runtime environment
    * Lambda - serverless app function
    * CloudWatch EventBridge - serverless app function trigger
    * IAM - roles & security
    * AWS Systems Manager Parameter Store - credentials & app parameters
* Terraform - infrastructure-as-a-code code
* GitHub Actions - CI/CD pipeline
    * GitHub Action Secrets - AWS credentials & Terraform backend config required for infrastructure CD

## Getting Started

To get a copy up and running follow the steps below.

### Prepare

1. Telegram
    1. Create a Telegram bot. [Here is how](https://core.telegram.org/bots#3-how-do-i-create-a-bot)
    1. Make a note of the Telegram bot API token
    1. Create two Telegram chats: "dev" and "prod" through the Telegram app
    1. Include the bot as an Administrator into those chats through the Telegram app
    1. Learn group chat ids for the "dev" and "prod" chats. [Here is how](https://stackoverflow.com/questions/32423837/telegram-bot-how-to-get-a-group-chat-id)

1. AWS
    1. Create parameters in Parameter Store of the AWS Systems Manager service as in the picture
        1. Make use of the values noted above
        1. Use the same Telegram bot token for both "dev" and "prod" parameters
    1. Create a programmatic access user for the Terraform deployment in AWS IAM. Include it into AWS Administrators group (or try to narrow down the required permissions if you are to follow the best security practice)
    1. Take a note of the user's access key id and secret access key
    1. Create an S3 bucket for the Terraform state storage

    ![](https://github.com/mikevostrikov/2021-06-10-mvzoobot/blob/master/doc/aws_ssm_params.png?raw=true)

1. GitHub
    1. Fork this repo
    1. Configure GitHub Action Secrets with Terraform user access key id and secret access key and the bucket name as in the picture
    
    ![](https://github.com/mikevostrikov/2021-06-10-mvzoobot/blob/master/doc/github_actions_params.png?raw=true)

### Deployment

AWS resources are created in the `us-east-1` region.

There are two environments implied: `dev` and `prod`. Resources names are suffixed with the name of the environment.

Commit to the `master` branch of the GitHub repo will initiate deployment to the "dev" environment. After the automatic deployment you will get a working solution, pushing the tickets notifications into the "dev" Telegram chat.

Commit to the `release` branch of the GitHub repo will initiate deployment to the "prod" environment. The notifications will be pushed into the "prod" Telegram chat.


## License

This program is free software. It comes without any warranty, to the extent permitted by applicable law. You can redistribute it and/or modify it under the terms of the Do What The F* You Want To Public License, Version 2, as published by Sam Hocevar. See http://www.wtfpl.net/ for more details.