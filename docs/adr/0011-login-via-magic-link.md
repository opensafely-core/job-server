# 11. Adding a magic link login flow
Date: 2023-03-13

## Status
Accepted

## Context
Our current user base writes code to use the platform, and we require that the code is hosted on GitHub.
Users are required to have an account with GitHub to use it.
Because we can rely on users having an account there we use GitHub OAuth for authentication to job-server.

For OSI v2 we are inviting less technical users to try out the platform.
These users will be signing up to use our interactive form, and won't be expected to write code to access the benefits of the platform.
Since these users will not be writing code there is no expectation or guarantee they will have a GitHub account, or even know what GitHub is.
We expect our current GitHub OAuth flow, and the need to sign up for a GitHub account, to cause confusion with this new type of user.

We want to avoid storing passwords because of the extra complexity and risk we will gain.
Django provides various tools to make this easier but the onus is still on us to keep up to date with those tools and changes in the security landscape.


## Decision
We will use "magic links" emailed to a valid user's email address.

The login page will have a form added for users to submit their email address to get a login link.
Unknown email addresses will fail silently to avoid leaking user account details.

For users who have an attached GitHub account, and thus have signed in with GitHub OAuth, we will email them to explain that they should log in with the GitHub button on the login page, and link them back to the login page.

To start with we will only allow users with the `InteractiveReporter` role to get the magic link login email.

For valid users we will create a secret token, storing it along with the email address in the user's session.
The email itself will contain the token, signed using Django's TimestampSigner so we can apply a timeout.

When the user clicks this link we will check the validity of the token in the URL, and that it has not expired, look up the user via the email address in the session, and finally delete both token and email from the session.
This makes the magic link single use from a successful login.

There are various error cases, which we'll log to our general logs, Sentry, and Honeycomb.
This will allow us to track elevated error rates.

## Consequences
Using the session means the magic link can only be used in the same browser it was requested in.
This stops email client previews from expiring the link.
While we have mentioned this in the error message it could potentially add some friction and confusion for users.

We expect there to be other classes of user in the future for which GitHub OAuth doesn't make sense as their authentication method.
This may be useful for those use cases
