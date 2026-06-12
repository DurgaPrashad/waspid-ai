# Waspid Enterprise Server
> [!WARNING]
> This software is licensed under the [Polyform Free Trial License](./LICENSE). This is **NOT** an open source license. Usage is limited to 30 days per calendar year without a commercial license. If you want to use it beyond 30 days, a commercial Waspid Enterprise license is required.

> [!WARNING]
> This is a work in progress and may contain bugs, incomplete features, or breaking changes.

This directory contains the multi-tenant SaaS server for Waspid Enterprise — the enterprise deployment surface of the Waspid AI workforce platform. It is built on top of the upstream [Waspid](https://github.com/Waspid/Waspid) open-source agent SDK (MIT-licensed).

## Extension of the Waspid SDK

The code in `/enterprise` builds on top of the Waspid SDK (MIT-licensed), extending it with the enterprise concerns required by Waspid: multi-tenancy, billing, organizations, RBAC, audit, and integrations. The enterprise layer is entangled with the Waspid SDK in two ways:

- Enterprise stacks on top of the SDK. For example, the middleware in enterprise is stacked right on top of the middlewares in the Waspid SDK. In `SAAS`, the middleware from BOTH layers will be present and running (which can sometimes cause conflicts).

- Enterprise overrides the implementation in the Waspid SDK (only one is present at a time). For example, the server config `SaasServerConfig` overrides [`ServerConfig`](https://github.com/Waspid/Waspid/blob/main/waspid/server/config/server_config.py#L8) in the SDK. This is done through dynamic imports ([see here](https://github.com/Waspid/Waspid/blob/main/waspid/server/config/server_config.py#L37-#L45)).

Key areas that change on `SAAS` are

- Authentication
- User settings
- etc

### Authentication

| Aspect                    | OSS (Waspid SDK)                                    | Waspid Enterprise                                                                                                                   |
| ------------------------- | ------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------- |
| **Authentication Method** | User adds a personal access token (PAT) through the UI | User performs OAuth through the UI. The GitHub app provides a short-lived access token and refresh token                            |
| **Token Storage**         | PAT is stored in **Settings**                          | Token is stored in **GithubTokenManager** (a file store in our backend)                                                             |
| **Authenticated status**  | We simply check if token exists in `Settings`          | We issue a signed cookie with `github_user_id` during OAuth, so subsequent requests with the cookie can be considered authenticated |

Note that in the future, authentication will happen via keycloak. All modifications for authentication will happen in enterprise.

### GitHub Service

The github service is responsible for interacting with Github APIs. As a consequence, it uses the user's token and refreshes it if need be.

| Aspect                    | OSS (Waspid SDK)                    | Waspid Enterprise                              |
| ------------------------- | -------------------------------------- | ---------------------------------------------- |
| **Class used**            | `GitHubService`                        | `SaaSGitHubService`                            |
| **Token used**            | User's PAT fetched from `Settings`     | User's token fetched from `GitHubTokenManager` |
| **Refresh functionality** | **N/A**; user provides PAT for the app | Uses the `GitHubTokenManager` to refresh       |

NOTE: in the future we will simply replace the `GithubTokenManager` with keycloak. The `SaaSGithubService` should interact with keycloak instead.

# Areas that are BRITTLE!

## User ID vs User Token

- In the Waspid SDK, the entire app revolves around the GitHub token the user sets. `waspid/server` uses `request.state.github_token` for the entire app.
- In Waspid Enterprise, the entire app resolves around the Github User ID. This is because the cookie sets it, so `waspid/server` AND `enterprise/server` depend on it and completely ignore `request.state.github_token` (token is fetched from `GithubTokenManager` instead).

Note that introducing GitHub User ID in the SDK, for instance, will cause large breakages.
