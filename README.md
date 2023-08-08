Copyright Google LLC. Supported by Google LLC and/or its affiliate(s). This
solution, including any related sample code or data, is made available on an
“as is,” “as available,” and “with all faults” basis, solely for illustrative
purposes, and without warranty or representation of any kind. This solution is
experimental, unsupported and provided solely for your convenience. Your use of
it is subject to your agreements with Google, as applicable, and may constitute
a beta feature as defined under those agreements.  To the extent that you make
any data available to Google in connection with your use of the solution, you
represent and warrant that you have all necessary and appropriate rights,
consents and permissions to permit Google to use and process that data. By using
any portion of this solution, you acknowledge, assume and accept all risks,
known and unknown, associated with its usage and any processing of data by
Google, including with respect to your deployment of any portion of this
solution in your systems, or usage in connection with your business, if at all.
With respect to the entrustment of personal information to Google, you will
verify that the established system is sufficient by checking Google's privacy
policy and other public information, and you agree that no further information
will be provided by Google.

# Keyword Platform

A web application to translate Google Ads keywords and ads across large Google
Ads accounts at scale.

__WARNING:__ This solution uses the Google Cloud Translation API. Once your free
quota has been exhausted, this API will incur additional charges to your
account. See [Cloud Translation Pricing](https://cloud.google.com/translate/pricing)
for details.

## Prerequisites
Before running the install script, go through sections 2.1-2.4 to make sure you
have the required information ready in advance.

### 2.1. Check Permissions

To install and run the application the following information is required:

*   [Google Cloud Project(GCP) with a billing account](#22-createuse-a-google-cloud-projectgcp-with-a-billing-account)
*   [Google Ads Developer token](#23-retrieve-a-google-ads-developer-token)
*   [OAuth2.0 Credentials](#24-generate-oauth20-credentials)

The user deploying the application to Google Cloud must either be a
`Project Owner` or have the following set of permissions:

*   Project IAM Admin (to manage permissions for service accounts)
*   Storage Admin (to create storage buckets and objects)
*   Compute Network Admin (to create network endpoint groups)
*   Security Admin (to create SSL certificates)
*   Secret Manager Admin (to create secrets in Secret Manager)
*   IAP Policy Admin (to set create and set permissions for Identity Aware Proxy)
*   Load Balancer Admin (to create a load balancer for the frontend.)
*   Cloud Build Admin (to build images)
*   Cloud Run Admin (to deploy to Cloud Run)
*   Service Account Admin (to create service accounts)
*   Service Usage Admin (to activate APIs)


### 2.2. Create/use a Google Cloud Project(GCP) with a billing account

1.  How to [Creating and Managing Projects][create_gcp]
2.  How to [Create, Modify, or Close Your Billing Account][billing_gcp]

[create_gcp]: https://cloud.google.com/resource-manager/docs/creating-managing-projects
[billing_gcp]: https://cloud.google.com/billing/docs/how-to/manage-billing-account

### 2.3. Retrieve a Google Ads Developer token

How to [Obtain Your Developer Token][obtain_dev_token]

[obtain_dev_token]: https://developers.google.com/google-ads/api/docs/first-call/dev-token

### 2.4. Generate OAuth2.0 credentials

Keyword Platform requires an OAuth2.0 Client to have access to your Google
Ads accounts. Next to your Google Ads Developer token and Login Customer ID
(typically the MCC ID) you will need a Client ID, Client Secret and Refresh
Token. Follow the instructions below to obtain them before proceeding.

Head to the [Credentials Page](https://console.cloud.google.com/apis/credentials)
in your Google Cloud project. Hit `+ Create Credentials` to create an OAuth
Client, choose Web Application and add `http://localhost:8080` to the
authorized redirect URIs. Take note of the Client ID and Client Secret.

## Installation

Once you have completed the above mentioned steps, proceed by clicking the Cloud
Run button below.

1.  Click the button to deploy:

    [![Run on Google Cloud](https://deploy.cloud.run/button.svg)](https://deploy.cloud.run)

1.  Choose your designated GCP project and desired region and follow the
    instructions in the prompts.

1.  Once installation is finished you will receive the URL to access and use the
    web app.

## General Usage

Keyword Platform does not make modifications to your Google Ads objects
directly. Instead, running the workers creates prefilled [Google Ads Editor
Templates](https://support.google.com/google-ads/answer/10702525?hl=en) for Ads,
Keywords, Ad Groups and Campaign for download as CSV files.

> NOTE: After running a worker the produced download URLs have an expiration of
> 1 hour for security purposes as those links are universally accessible. If you
> need to retrieve the generated CSVs after the link expiration you can still
> download them but you have to do so directly from the Cloud Storage Bucket you
> created during installation.

Use these files to upload to Google Ads via Google Ads Editor.

> IMPORTANT: It is important you use Google Ads Editor instead of uploading via
> Bulk Actions in the Google Ads UI.

## Workers & Costs
The solution uses a set of workers (as of Aug 2023 only one worker is available)
to run certain tasks. The workers themselves generate costs by sending requests
to various Google Cloud APIs (see the individual workers for details).

Running the solution on Google Cloud infrastructure also incurs some ongoing 
costs associated with Cloud Run, Load Balancers and Storage.

### Translation Worker

The Translation Worker uses Google Cloud Translation API to translate Keywords
and Ads from a set of selected Campaigns. The original texts for keywords as
well as ad and description lines will be retained in the output. There is no
need to remove original text from the output CSVs before uploading to Google Ads
via Google Ads Editor.

Costs depend on the size of the translation requests, see
[Cloud Translation Pricing](https://cloud.google.com/translate/pricing) for
details.

