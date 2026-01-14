# 0001a - Context View (C4 Level 1)

The system context diagram shows Aletheia's boundary and its interactions with external actors and systems.

```mermaid
graph TB
    subgraph Users
        User((End User))
        Dev((Developer))
    end

    subgraph Aletheia [Aletheia System]
        Ext[Browser Extension]
        Backend[Lambda Backend]
    end

    subgraph External [External Systems]
        Chrome[Chrome Web Store]
        Firefox[Firefox Add-ons]
        AWS[AWS Cloud]
        Bedrock[Amazon Bedrock]
    end

    subgraph Data [Data Sources]
        Wiki[Wikipedia Denylist]
    end

    User -->|selects text| Ext
    User -->|configures allowlist| Ext
    Ext -->|API calls| Backend
    Backend -->|LLM inference| Bedrock
    Backend -->|state persistence| AWS

    Dev -->|deploys| Backend
    Dev -->|submits| Chrome
    Dev -->|submits| Firefox

    Chrome -.->|distributes| Ext
    Firefox -.->|distributes| Ext
    Wiki -.->|feeds| Backend
```

## External Actors

| Actor | Description | Interaction |
|-------|-------------|-------------|
| **End User** | Browser user who selects text for analysis | Triggers analysis, configures site allowlist |
| **Developer** | Maintains and deploys the system | Deploys Lambda, submits to stores |

## External Systems

| System | Purpose | Integration |
|--------|---------|-------------|
| **Chrome Web Store** | Distribution for Chrome extension | Manual submission via developer dashboard |
| **Firefox Add-ons** | Distribution for Firefox extension | Manual submission via AMO dashboard |
| **Amazon Bedrock** | LLM inference (Amazon Nova Micro) | boto3 SDK, invoke_model API |
| **AWS Cloud** | Hosting (Lambda, DynamoDB, API Gateway) | Infrastructure as Code via provision.sh |
| **Wikipedia** | Source for denylist terms (803 terms) | One-time harvest, static JSON in Lambda |

## Trust Boundaries

```mermaid
graph TB
    subgraph Untrusted [Untrusted Zone]
        User((User Input))
        HostPage[Host Page DOM]
    end

    subgraph SemiTrusted [Semi-Trusted Zone]
        Ext[Extension Content Script]
    end

    subgraph Trusted [Trusted Zone]
        SW[Service Worker]
        Lambda[Lambda Function]
        Bedrock[Bedrock]
    end

    User -->|text selection| Ext
    HostPage -->|DOM context| Ext
    Ext -->|sanitized request| SW
    SW -->|HTTPS| Lambda
    Lambda -->|invoke| Bedrock
```

| Boundary | What Crosses | Validation |
|----------|--------------|------------|
| User → Extension | Raw text selection | XML escaping, length limits |
| Host Page → Extension | DOM context | Shadow DOM isolation |
| Extension → Lambda | JSON payload | Schema validation, rate limiting |
| Lambda → Bedrock | Prompt | Prompt injection protection |

---

[← Back to Architecture](0001-architecture.md) | [Container View →](0001b-container-view.md)
