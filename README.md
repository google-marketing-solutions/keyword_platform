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

> [!WARNING]
> This solution uses the Google Cloud Translation API. Once your free quota has
> been exhausted, this API will incur additional charges to your account.
> See [Cloud Translation Pricing](https://cloud.google.com/translate/pricing)
> for details.

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

> [!IMPORTANT]
> Ensure the user going through the OAuth flow has standard access to the Google
> Ads accounts you want to use from within the web app.

## Installation

Once you have completed the above mentioned steps, proceed by clicking the Open
in Cloud Shell button below.

> [!IMPORTANT]
> To use GenAI features you have to choose `us-central1` as region.

1.  Click the button to deploy:

    [![Open in Cloud Shell](https://gstatic.com/cloudssh/images/open-btn.svg)](https://shell.cloud.google.com/cloudshell/editor?cloudshell_git_repo=https%3A%2F%2Fgithub.com%2Fgoogle-marketing-solutions%2Fkeyword_platform&cloudshell_git_branch=main&cloudshell_tutorial=setup%2Fdocs%2Finstall.md&show=terminal)

1.  Follow the instructions.

1.  Once installation is finished you will receive the URL to access and use the
    web app.

## General Usage

Keyword Platform does not make modifications to your Google Ads objects
directly. Instead, running the workers creates prefilled [Google Ads Editor
Templates](https://support.google.com/google-ads/answer/10702525?hl=en) for Ads,
Keywords, Ad Groups and Campaign for download as CSV files.

> [!NOTE]
> After running a worker the produced download URLs have an expiration of
> 1 hour for security purposes as those links are universally accessible. If you
> need to retrieve the generated CSVs after the link expiration you can still
> download them but you have to do so directly from the Cloud Storage Bucket you
> created during installation.

Use these files to upload to Google Ads via Google Ads Editor.

> [!IMPORTANT]
> It is important you use Google Ads Editor instead of uploading via Bulk
> Actions in the Google Ads UI.

## Access Management

You can provide a list of user emails during the installation to grant access
to the web application. You can continue to manage access to the web app via
the Cloud Console by heading to [Identity Aware Proxy](https://console.cloud.google.com/security/iap)
in the Google Cloud Project that was used for the deployment.

Under `Backend Services` click on the `keywordplatform-frontend-backend-service`
resource. This opens a menu on the right side of your screen with the
`ADD PRINCIPAL` button. Using this button you can add or remove users by
granting or revoking the `Cloud IAP > IAP-secured Web App User` role.

> [!NOTE]
> To make access management easier you can also grant email groups, e.g. a
> [Google Groups](https://groups.google.com) access to the Web App.

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

### Glossaries

The solution supports [unidirectional Glossaries](https://cloud.google.com/translate/docs/advanced/glossary#format-glossary),
which will be automatically created when uploaded file to a dedicated cloud
storage bucket (`gs://my-project-glossaries`). Glossary CSV files **MUST**
adhere to the following naming convention:

`[source-language-code]-to-[target-language-code]-[your-glossary-name].csv`

e.g. `en-to-de-brandterms.csv`

## FAQs & Troubleshooting

1.  **How do I stop certain terms (e.g., brand terms) from being translated?**

    This can be avoided by using Glossaries, which are supported by Keyword
    Platform. During installation a dedicated bucket for glossary files is
    generated to which you can upload [unidirectional glossary files](https://cloud.google.com/translate/docs/advanced/glossary#unidirectional_glossaries). They will
    automatically be picked up by a pub/sub subscription and processed, which
    creates a glossary entry in your Google Cloud project. When running
    translations you can select the glossary you want to apply from an optional
    dropdown.

1.  **How can I add terms to a glossary via the UI?**

    This functionality is currently not available, but glossary entries are
    overwritten by default. To update a previously generated glossary, simply
    upload a new file with the same name containing previous and newly added
    terms.

1.  **Why are there no accounts in the account dropdown?**

    This is likely due to credentials not being valid. To get more details, you
    can check the logs by going to `Logs Explorer` in the Google Cloud Console.
    To generate new credentials you can either run the installation again
    (`./setup/install.sh`) or manually create new credentials using the [oauth
    playground](https://developers.google.com/oauthplayground/). To do that, you
    need to:
    *   Add `https://developers.google.com/oauthplayground`` to the `Authorized
        redirect URIs` in your OAuth2.0 client in the Google Cloud Console under
        `APIs & Services > Credentials`.
    *   On the [oauth playground page](https://developers.google.com/oauthplayground/)
        add the client id and secret under `Settings > Use your own OAuth
        credentials`.
    *   Select all the [required scopes](https://github.com/google-marketing-solutions/keyword_platform/blob/main/setup/utils/oauth_flow.py#L41).
    *   Hit `Authorize APIs` and exchange the access token for a refresh token.
    *   In Google Cloud Console head to `Secret Manager` and update the secrets
        accordingly.

1.  **Why am I getting a `Http failure …/proxy: 500 OK` response after hitting
    the RUN button?**

    There can be various reasons for this and the logs will give you more
    details as to what happened. Head to your Cloud Console `Logs Explorer`
    and investigate any errors.

1.  **When logging into my Google Account during installation I get "Access
    blocked: This app's request is invalid".**

    Make sure to have added http://localhost:8080 to the `Authorized redirect
    URIs`` in your OAuth2.0 client in the Google Cloud Console under `APIs &
    Services > Credentials`.

1.  **During installation terraform command fails with `error creating Brand:
    googleapi: Error 409: Requested entity already exists`.**

    We use terraform for installation and setting up the Google Cloud resources.
    Terraform only supports internal OAuth Consent Screens. Before installing
    Keyword Platform, ensure that your OAuth Consent Screen is set to `internal`.

1. **Installation failed, what are my options?**

    The installation script `setup/install.sh` accomplishes the following set of
    tasks:
    1.      Ensure that certain APIs are enabled.
    1.      Create a terraform state bucket
    1.      Build the frontend and backend images from Dockerfiles.
    1.      Execute the oAuth2.0 flow to gain a refresh token.
    1.      Runs terraform with a set of variables collected from user input.

    If any of the steps between 1 and 3 fail, the most common reason is that
    your user doesn't have the required permissions - ensure you have `Project
    Owner` permissions. For troubleshooting Step 4, see some of the FAQs above.
    If there are errors in Step 5, you do not need to run the entire
    installation script again, which can take time, because it will build to
    front- and backend images from Dockerfiles which can take some time. Instead
    you can run the terraform commands manually as follows:

    1.  Ensure you have cloned the repository and navigated to the 
        `keyword-platform` directory: `cd keyword-platform`.

    2.  Run the following command replacing the variable values, this sets
        a range of environment variables which will make it easier to run
        commands in subsequent steps:

        ```shell
        backend_image=gcr.io/${GOOGLE_CLOUD_PROJECT}/keywordplatform-backend && \
        frontend_image=gcr.io/${GOOGLE_CLOUD_PROJECT}/keywordplatform-frontend && \
        terraform_state_bucket_name=${GOOGLE_CLOUD_PROJECT}-bucket-tfstate && \
        OPT_OUT=false &&
        BUCKET_NAME=<enter-bucket-name> && \
        CLIENT_ID=<your-client-id> && \
        CLIENT_SECRET=<your-client-secret> && \
        DEVELOPER_TOKEN=<your-developer-token> && \
        LOGIN_CUSTOMER_ID=<your-login-customer-id> && \
        IAP_ALLOWED_USERS=<your-email> && \
        IAP_SUPPORT_EMAIL=<your-email> && \
        iap_brand_id=$(gcloud iap oauth-brands list --format="value(name)" | sed "s:.*/::") && \
        support_email=$(gcloud iap oauth-brands list --format="value(supportEmail)") && \
        allowed_users_tf_list=$(echo "$IAP_ALLOWED_USERS" | sed 's/\([^,]\+\)/"user:\1"/g' | sed 's/,/, /g' | sed 's/.*/[&]/') && \
        refresh_token=<your-refresh-token> && \
        GOOGLE_CLOUD_REGION=us-central1
        ```
        If you don't have access to a refresh token, you can create one manually
        by following instruction under *"Why are there no accounts in the account
        dropdown?"* above.

    3.  If you previously ran the installation script and the front- and backend
        images were built successfully, you can skip this step.

        Build the frontend- and backend images.

        ```shell
        gcloud builds submit ./py \ --tag $backend_image
        gcloud builds submit ./ui \--tag $frontend_image
        ```

    4.  Initialize terraform

        ```shell
        terraform -chdir=./terraform init \
            -backend-config="bucket=$terraform_state_bucket_name" \
            -get=true \
            -upgrade \
            -reconfigure
        ```
    5.  Create a terraform plan:

        ```shell
        terraform -chdir=./terraform plan \
            -var "bucket_name=$BUCKET_NAME" \
            -var "frontend_image=$frontend_image" \
            -var "backend_image=$backend_image" \
            -var "client_id=$CLIENT_ID" \
            -var "opt_out=$OPT_OUT" \
            -var "client_secret=$CLIENT_SECRET" \
            -var "developer_token=$DEVELOPER_TOKEN" \
            -var "login_customer_id=$LOGIN_CUSTOMER_ID" \
            -var "refresh_token=$refresh_token" \
            -var "project_id=$GOOGLE_CLOUD_PROJECT" \
            -var "region=$GOOGLE_CLOUD_REGION" \
            -var "iap_allowed_users=$allowed_users_tf_list" \
            -var "iap_support_email=$support_email" \
            -var "iap_brand_id=$iap_brand_id" \
            -out="/tmp/tfplan"
        ```
    6.  Check the plan! If everything looks good execute the plan:

        ```shell
        terraform -chdir=./terraform apply "/tmp/tfplan"
        ```


## Privacy Notice

> [!NOTE]
> By using this solution you agree for usage, device and location data be
> collected automatically. If you don't want this information to be collected
> you can opt-out during installation or refrain from using the solution.

We automatically collect certain information when you visit, use or navigate the
Keyword Platform website. This information does not reveal your specific
identity (like your name or contact information) but may include device and
usage information, such as your IP address, browser and device characteristics,
operating system, language preferences, referring URLs, device name, country,
location, information about how and when you use the Keyword Platform website,
and other technical information. This information is primarily needed to
maintain the security and operation of the Keyword Platform solution, and for
our internal analytics and reporting purposes.

The information we collect includes:

*	Log and Usage Data. Log and usage data is service-related, diagnostic,
usage, and performance information automatically collected when you access or
use a website created by this solution. Depending on how you interact with the
Keyword Platform website, this log data may include your IP address, device
information, browser type, and settings and information about your activity on
the Keyword Platform website (such as the date/time stamps associated with your
usage, pages, and files downloaded, and other actions you take such as which
features you use), device event information (such as systems activity, error
reports (sometimes called “crash dumps”), and hardware settings). We also
collect information about Google Ads accounts and campaigns connected to the
Keyword Platform service (such as account and campaign IDs as well as campaign
settings such as bid strategy, target network and others). We also collect
information about the size of the requests sent to API endpoints such as Cloud
Translation API and VertexAI API as well as information about the originating
Cloud Project (such as project ID and name).

*	Device Data. We collect device data such as information about your computer,
phone, tablet, or other devices you use to access the Keyword Platform website.
Depending on the device used, this device data may include information such as
your IP address (or proxy server), device and application identification numbers,
location, browser type, hardware model, internet service provider and/or mobile
carrier, operating system, and system configuration information.

*	Location Data. We collect location data such as information about your
device’s location, which can be either precise or imprecise. How much
information we collect depends on the type and settings of the device you use
to access the Keyword Platform website. For example, we may use GPS and other
technologies to collect geolocation data that tells us your current location
(based on your IP address).

We do not collect and personal information such as email, name or phone number.

We process your personal information to identify usage trends. We may process
information about how you use our Services to better understand how they are
being used so we can improve them.
