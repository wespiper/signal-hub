# Signal Hub Editions

Signal Hub is available in multiple editions to meet different needs and scale requirements.

## Signal Hub Basic (Open Source)

The community edition provides core functionality for extending Claude's context through RAG, suitable for individual developers and small teams.

### Features Included

#### Core Infrastructure
- ✅ **MCP Server Integration**: Seamless connection with Claude Code
- ✅ **Codebase Indexing**: Automatic scanning and indexing of your codebase
- ✅ **Semantic Search**: Find relevant code using natural language queries
- ✅ **Basic RAG**: Retrieval-augmented generation for context assembly

#### Cost Optimization
- ✅ **Simple Model Routing**: Rule-based routing between Haiku, Sonnet, and Opus
- ✅ **Semantic Caching**: Cache similar queries for instant responses
- ✅ **Manual Escalation**: Override model selection when needed
- ✅ **Basic Cost Tracking**: Monitor your AI model usage costs

#### Developer Experience
- ✅ **Zero Configuration**: Works out of the box with sensible defaults
- ✅ **Local Storage**: ChromaDB for vector storage
- ✅ **Simple Analytics**: Basic usage and cost reporting
- ✅ **Community Support**: GitHub issues and discussions

### Limitations
- ❌ No machine learning-based routing optimization
- ❌ No learning from user feedback
- ❌ Limited analytics and reporting
- ❌ No team collaboration features
- ❌ Basic caching strategies only

## Signal Hub Pro (Coming Soon)

Advanced features for power users and teams who want to maximize cost savings and efficiency.

### Additional Features

#### Intelligent Routing
- 🚀 **ML-Powered Model Selection**: Automatically choose the optimal model based on query complexity
- 🚀 **Learning Algorithms**: Improve routing decisions based on user feedback
- 🚀 **Personalized Routing**: Adapt to individual usage patterns
- 🚀 **Advanced Cost Optimization**: Save 70%+ on AI costs

#### Enhanced Analytics
- 📊 **Detailed Cost Reports**: Comprehensive breakdown of usage and savings
- 📊 **ROI Dashboard**: Track your return on investment
- 📊 **Usage Patterns**: Understand how your team uses AI
- 📊 **Performance Metrics**: Monitor response times and quality

#### Advanced Features
- ⚡ **Smart Caching**: Advanced semantic deduplication
- ⚡ **API Access**: REST API for custom integrations
- ⚡ **Custom Model Support**: Add your own AI models
- ⚡ **Priority Support**: Get help when you need it

### Pricing
- **$29/month** + 15% of cost savings above $100/month
- **Risk-free**: Only pay when you save money
- **Transparent**: Clear reporting on savings vs. subscription cost

## Signal Hub Enterprise (Coming Soon)

For large organizations requiring advanced security, compliance, and team features.

### Additional Features

#### Team & Security
- 👥 **Team Management**: User roles and permissions
- 🔐 **SSO Integration**: SAML/OIDC support
- 🔐 **Audit Logging**: Complete activity trails
- 🔐 **Advanced Security**: Encryption at rest and in transit

#### Deployment & Support
- 🏢 **Custom Deployment**: On-premise or private cloud options
- 🏢 **Dedicated Support**: SLA with guaranteed response times
- 🏢 **Professional Services**: Custom development and integration
- 🏢 **Training**: Onboarding and best practices workshops

### Pricing
- **Custom pricing** based on usage and requirements
- **Volume discounts** available
- **10% of cost savings** (lower percentage than Pro)
- **Annual contracts** with flexible terms

## Early Access Program

We're currently in early access mode where all features are available to help us refine the product and pricing model.

### How to Join
1. **Use Signal Hub Basic**: Start with the open source version
2. **Enable Early Access**: Set `SIGNAL_HUB_EARLY_ACCESS=true`
3. **Provide Feedback**: Join our [Discord](https://discord.gg/signalhub) community
4. **Get Pro Features Free**: Access all features during early access

### Benefits
- 🎁 Free access to all Pro and Enterprise features
- 🗣️ Direct input on product development
- 🏆 Recognition as an early supporter
- 💰 Discounted pricing when we launch

## Feature Comparison

| Feature | Basic | Pro | Enterprise |
|---------|-------|-----|------------|
| **Core Features** |
| MCP Server | ✅ | ✅ | ✅ |
| Codebase Indexing | ✅ | ✅ | ✅ |
| Semantic Search | ✅ | ✅ | ✅ |
| Basic RAG | ✅ | ✅ | ✅ |
| **Routing & Optimization** |
| Rule-based Routing | ✅ | ✅ | ✅ |
| ML-powered Routing | ❌ | ✅ | ✅ |
| Learning Algorithms | ❌ | ✅ | ✅ |
| Personalized Routing | ❌ | ✅ | ✅ |
| **Caching & Performance** |
| Basic Caching | ✅ | ✅ | ✅ |
| Smart Deduplication | ❌ | ✅ | ✅ |
| Predictive Caching | ❌ | ✅ | ✅ |
| **Analytics & Reporting** |
| Basic Cost Tracking | ✅ | ✅ | ✅ |
| Detailed Analytics | ❌ | ✅ | ✅ |
| ROI Dashboard | ❌ | ✅ | ✅ |
| Custom Reports | ❌ | ❌ | ✅ |
| **Team Features** |
| Single User | ✅ | ✅ | ✅ |
| Team Sharing | ❌ | Limited | ✅ |
| User Management | ❌ | ❌ | ✅ |
| Role-based Access | ❌ | ❌ | ✅ |
| **Security & Compliance** |
| Local Storage | ✅ | ✅ | ✅ |
| Cloud Storage | ❌ | ✅ | ✅ |
| SSO Integration | ❌ | ❌ | ✅ |
| Audit Logging | ❌ | ❌ | ✅ |
| **Support** |
| Community Support | ✅ | ✅ | ✅ |
| Priority Support | ❌ | ✅ | ✅ |
| Dedicated Support | ❌ | ❌ | ✅ |
| SLA | ❌ | ❌ | ✅ |
| **Deployment** |
| Self-hosted | ✅ | ✅ | ✅ |
| Cloud Managed | ❌ | ✅ | ✅ |
| On-premise | ❌ | ❌ | ✅ |
| Custom Deployment | ❌ | ❌ | ✅ |

## Migration Path

### From Basic to Pro
1. **Install Pro Components**: `pip install signal-hub[pro]`
2. **Update Configuration**: Set `edition: "pro"` in config
3. **Add License Key**: Configure your license in settings
4. **Enable Features**: Pro features activate automatically

### From Pro to Enterprise
1. **Contact Sales**: Discuss your requirements
2. **Custom Setup**: We'll help configure for your needs
3. **Migration Support**: Full assistance with transition
4. **Training**: Onboarding for your team

## Frequently Asked Questions

### Can I start with Basic and upgrade later?
Yes! Signal Hub is designed for seamless upgrades. Your data, configuration, and integrations remain intact when upgrading.

### Is the Basic edition really free forever?
Yes, Signal Hub Basic is open source (MIT license) and will always be free to use.

### How do you calculate cost savings?
We compare the cost of queries routed to efficient models (Haiku/Sonnet) versus always using the most expensive model (Opus).

### Can I self-host the Pro edition?
Yes, Pro edition can be self-hosted with a valid license key.

### What happens to my data when I upgrade?
All your indexed data, settings, and history are preserved during upgrades.

## Get Started

1. **Try Signal Hub Basic**: [Installation Guide](../README.md#quick-start)
2. **Enable Early Access**: Get Pro features free during our beta
3. **Join the Community**: [Discord](https://discord.gg/signalhub) | [GitHub Discussions](https://github.com/wespiper/signal-hub/discussions)
4. **Stay Updated**: Star our [GitHub repo](https://github.com/wespiper/signal-hub) for updates