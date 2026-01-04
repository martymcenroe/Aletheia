# Aletheia: AI-Powered Context Analysis Engine

# Add after the first heading in README.md
# You'll need to enable Codecov integration at codecov.io first

BADGES='
![CI](https://github.com/martymcenroe/Aletheia/actions/workflows/ci.yml/badge.svg)
[![codecov](https://codecov.io/gh/martymcenroe/Aletheia/branch/main/graph/badge.svg)](https://codecov.io/gh/martymcenroe/Aletheia)
![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
'
echo "$BADGES"

**Aletheia** (Greek for *Truth/Unconcealment*) is a serverless, event-driven architecture that bridges the gap between static content and semantic understanding. It allows users to extract context-aware insights from any webpage using a custom Chrome Extension and an Agentic AI backend.

### 🏆 Engineering Highlights
* **Serverless Architecture:** Built on **AWS Lambda** and **DynamoDB** with "Scale-to-Zero" economics.
* **AI Agent Orchestration:** Implements **LangGraph** for stateful, multi-turn reasoning (not just stateless API calls).
* **Infrastructure as Code:** "Bare metal" provisioning scripts (Bash/AWS CLI) demonstrating deep understanding of cloud primitives without abstraction layers.
* **Event-Driven Harvesting:** Custom-built data pipeline to harvest, sanitize, and checkpoint training data from live browsing sessions.
* **Security First:** Strict IAM scoping and manifest permission gating.

### 🛠 Tech Stack
* **Language:** Python 3.12 (Backend), JavaScript (Frontend)
* **Cloud:** AWS (Lambda, DynamoDB, S3, IAM)
* **AI/ML:** LangChain, LangGraph, OpenAI/Bedrock
* **Tooling:** Poetry, GitHub Actions, Custom Bash Automation

### 🚀 Quick Start (Development)
1.  **Clone:** `git clone ...`
2.  **Provision:** `./provision.sh` (Sets up AWS resources)
3.  **Deploy:** `./deploy.sh` (Builds & pushes Lambda artifact)
4.  **Install:** Load `extension/` directory into Chrome Developer Mode.

---
*Created by [Marty McEnroe]. This project demonstrates strict engineering hygiene, architectural documentation, and the "AI-as-Workforce" development paradigm.*
