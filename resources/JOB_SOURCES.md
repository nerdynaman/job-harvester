# Engineering job sources and company careers directory

Compiled from the discussion through 24 November 2026 for a personal backend, AI, data engineering, and large-scale processing job digest. The directory covers 13 discovery sources, four employer-board APIs, and 82 employers. AWS, Google Cloud, and Azure appear under their parent employers. Search terms below describe areas to investigate. Hiring locations, active vacancies, and individual feed availability need checking when collecting.

## Job boards and discovery sources

| Source | Coverage | Collection method and access |
|---|---|---|
| [LinkedIn Jobs](https://www.linkedin.com/jobs/) | Broad product-company and multinational hiring | Sign in to configure [saved-search emails](https://www.linkedin.com/help/linkedin/answer/a511279/job-alerts-on-linkedin?lang=en). Process your own alerts via mailbox OAuth. The [Job Posting API](https://learn.microsoft.com/en-us/linkedin/talent/job-postings/api/overview) serves publishing partners. A candidate session does not grant bulk search access. [User agreement](https://www.linkedin.com/legal/user-agreement) |
| [Indeed](https://www.indeed.com/) | Cross-industry and location-based search | Configure [account-based email alerts](https://www.indeed.com/help/job-seekers/articles/204488890-starting-stopping-and-managing-job-alerts). Indeed also documents a publisher search plugin and provisioned partner integrations. Job Sync handles employer postings. [Partner docs](https://docs.indeed.com/) |
| [Naukri](https://www.naukri.com/) | Indian product companies and MNCs | Set up alerts by role, experience, and location. Read your own alert emails. [Alert setup](https://resume.naukri.com/frequently-asked-questions-faq/how-to-create-free-job-alerts/) |
| [Adzuna](https://developer.adzuna.com/overview) | Search across employers in supported countries | Register for an app ID and key. Query the paginated jobs API by country, role, and location. |
| [Himalayas](https://himalayas.app/docs/remote-jobs-api) | Remote engineering jobs | Read its public jobs API or [RSS feed](https://himalayas.app/docs/remote-jobs-rss). Check country eligibility. |
| [We Work Remotely](https://weworkremotely.com/remote-job-rss-feed) | Remote jobs by category | Read the public all-jobs or category RSS feed. Verify geographic restrictions per vacancy. |
| [Remotive](https://remotive.com/remote-jobs/api) | Remote engineering | Read its public API. The public feed is delayed by 24 hours and has attribution and reuse conditions. |
| [Hacker News “Who is hiring?”](https://news.ycombinator.com/submitted?id=whoishiring) | Monthly hiring-manager posts, including database and AI teams | Find the monthly hiring thread and fetch comments with the [public HN API](https://github.com/HackerNews/API). Follow employer links where available. |
| [YC Work at a Startup](https://www.ycombinator.com/jobs) | YC startups, including AI and data infrastructure | Use job search for employer discovery, then save each employer’s careers board. [India search](https://www.ycombinator.com/jobs/role/all/india) |
| [Wellfound](https://wellfound.com/jobs) | Startup engineering | Discover companies via job search and resolve listings to their careers pages. |
| [Instahyre](https://www.instahyre.com/) | India-focused technology hiring | Use account and discovery features to find employers and follow direct openings. |
| [Cutshort](https://cutshort.io/jobs) | Indian technology and product roles | Use job search to identify employers and save their careers pages. |
| [hirist.tech](https://www.hirist.tech/) | Indian IT and engineering roles | Discover employers through search and follow direct listings where available. |

## Public employer-board APIs

Each request reads one employer’s published board. Supply the identifier from that employer’s board URL. These listing routes can be read without a candidate login.

| Platform | Request | Collection notes |
|---|---|---|
| [Greenhouse](https://developers.greenhouse.io/job-board.html) | `GET https://boards-api.greenhouse.io/v1/boards/{board_token}/jobs?content=true` | Include descriptions for matching. Example tokens from the watchlist include `grafanalabs`, `anthropic`, and `cloudflare`. |
| [Lever](https://github.com/lever/postings-api) | `GET https://api.lever.co/v0/postings/{site}?mode=json` | Extract the site name from the hosted board, follow pagination, and use the EU API host for EU boards. |
| [Ashby](https://developers.ashbyhq.com/docs/public-job-posting-api) | `GET https://api.ashbyhq.com/posting-api/job-board/{board_name}` | Example names include `openai` and `perplexity`. Add `?includeCompensation=true` for published compensation where available. |
| [SmartRecruiters](https://developers.smartrecruiters.com/reference/v1listpostings) | `GET https://api.smartrecruiters.com/v1/companies/{companyIdentifier}/postings` | Page through the employer’s active postings and fetch individual posting details for full descriptions. |

For custom portals, look for a documented feed or native job alert. Where automated access is permitted, discover vacancy URLs through the public careers listings or sitemap, then read any `JobPosting` JSON-LD on the vacancy detail page. A careers link alone does not establish bulk access or redistribution rights. [JobPosting documentation](https://developers.google.com/search/docs/appearance/structured-data/job-posting)

## Company watchlist

### Databases, streaming, and data engineering

| Employer and career page | Suggested search terms |
|---|---|
| [Databricks](https://www.databricks.com/company/careers/open-positions) | Spark, lakehouse, query execution |
| [Snowflake](https://careers.snowflake.com/us/en) | Cloud warehouse, query optimizer, storage |
| [Confluent (IBM)](https://www.ibm.com/careers/search?q=confluent) | Kafka, Flink, stream processing |
| [MongoDB](https://www.mongodb.com/company/careers) | Database internals, replication, distributed storage |
| [Cockroach Labs](https://www.cockroachlabs.com/careers/open-positions/) | Distributed SQL, transactions, replication |
| [Elastic](https://jobs.elastic.co/) | Search, indexing, distributed systems |
| [ClickHouse](https://clickhouse.com/company/careers) | Columnar storage, query execution, analytical databases |
| [Redpanda](https://www.redpanda.com/careers) | Event streaming, Kafka-compatible systems, distributed storage |
| [ScyllaDB](https://www.scylladb.com/company/careers/) | Database internals, C++, low-latency distributed systems |
| [Starburst](https://www.starburst.io/careers/) | Trino, distributed SQL, query optimization, data lakehouse |
| [Fivetran](https://www.fivetran.com/careers) | Change data capture, database replication, ingestion pipelines |
| [Couchbase](https://www.couchbase.com/careers/) | Distributed databases, indexing, replication, cloud database services |
| [SingleStore](https://www.singlestore.com/careers/) | Query engines, distributed transactions, real-time analytics |
| [Datadog](https://careers.datadoghq.com/) | Metrics, logs, traces, high-throughput ingestion, observability storage |

### Cloud, backend infrastructure, and networking

| Employer and career page | Suggested search terms |
|---|---|
| [Amazon (AWS)](https://www.amazon.jobs/en/) | Distributed systems, storage, data engineering |
| [Google (Google Cloud)](https://www.google.com/about/careers/applications/jobs/results/) | Data infrastructure, cloud backend, ML systems |
| [Microsoft (Azure)](https://careers.microsoft.com/) | Control plane, data plane, cloud databases, AI infrastructure |
| [Oracle (OCI)](https://careers.oracle.com/en/sites/jobsearch) | Cloud infrastructure, database internals, distributed services |
| [Cloudflare](https://job-boards.greenhouse.io/cloudflare) | Edge computing, networking, distributed storage |
| [Grafana Labs](https://job-boards.greenhouse.io/grafanalabs) | Telemetry ingestion, observability, time series |
| [Rubrik](https://www.rubrik.com/company/careers) | Data protection, storage engines, distributed systems |
| [Cisco](https://careers.cisco.com/global/en/home) | Network telemetry, distributed control planes, security infrastructure |
| [Akamai](https://www.akamai.com/careers) | Edge computing, content delivery, distributed networking |
| [Nutanix](https://careers.nutanix.com/en/) | Distributed storage, virtualization, cloud infrastructure |

### AI engineering, inference, and compute

| Employer and career page | Suggested search terms |
|---|---|
| [NVIDIA](https://www.nvidia.com/en-us/about-nvidia/careers/) | GPU performance, training infrastructure, inference |
| [OpenAI](https://jobs.ashbyhq.com/openai) | Model serving, inference runtime, training infrastructure |
| [Anthropic](https://job-boards.greenhouse.io/anthropic) | ML systems, inference, evaluation infrastructure |
| [Perplexity](https://jobs.ashbyhq.com/perplexity) | AI inference, retrieval, training platform |
| [Cohere](https://cohere.com/careers) | Model serving, enterprise retrieval, applied ML |
| [Mistral AI](https://mistral.ai/careers/) | Inference engineering, ML systems, applied AI |
| [Together AI](https://www.together.ai/careers) | Model inference, distributed training, GPU performance |
| [CoreWeave](https://www.coreweave.com/careers) | GPU cloud, Kubernetes, cluster scheduling, storage |
| [Cerebras Systems](https://www.cerebras.ai/join-us) | ML compilers, runtimes, AI compute systems |
| [Qualcomm](https://careers.qualcomm.com/careers) | On-device inference, AI runtimes, model optimization |

### Global product engineering, fintech, and marketplaces

| Employer and career page | Suggested search terms |
|---|---|
| [Salesforce](https://www.salesforce.com/company/careers/jobs/) | Multi-tenant backend, data platform, applied AI |
| [Atlassian](https://www.atlassian.com/company/careers/engineering) | Product backend, distributed services, search |
| [Uber](https://www.uber.com/us/en/careers/) | Marketplace backend, event streaming, ML platforms |
| [Apple](https://www.apple.com/careers/in/) | Services engineering, iCloud, data infrastructure, machine learning |
| [SAP](https://jobs.sap.com/en/) | HANA database, cloud runtime, enterprise data platforms |
| [ServiceNow](https://careers.servicenow.com/) | Platform backend, workflow engines, search, enterprise AI |
| [Adobe](https://careers.adobe.com/us/en) | Document services, analytics pipelines, applied AI |
| [Intuit](https://www.intuit.com/careers/) | Financial data platforms, backend services, ML engineering |
| [PayPal](https://careers.pypl.com/home/) | Payments backend, risk systems, transaction processing |
| [Mastercard](https://careers.mastercard.com/us/en) | Payment networks, fraud detection, real-time decision systems |
| [Stripe](https://stripe.com/careers) | Payments infrastructure, ledgers, developer APIs, data platforms |
| [Spotify](https://www.lifeatspotify.com/jobs) | Recommendations, experimentation, data infrastructure |
| [Airbnb](https://careers.airbnb.com/) | Search and ranking, marketplace backend, data platforms |

### India-focused product-company watchlist

| Employer and career page | Suggested search terms |
|---|---|
| [Flipkart](https://www.flipkartcareers.com/) | Search and recommendations, catalog, supply chain, event processing |
| [PhonePe](https://www.phonepe.com/careers/) | UPI, payment reliability, real-time risk, data platforms |
| [Razorpay](https://razorpay.com/careers/) | Payment APIs, ledgers, reconciliation, fraud systems |
| [Swiggy](https://careers.swiggy.in/) | Dispatch, logistics, forecasting, streaming data |
| [Meesho](https://www.meesho.io/jobs) | Marketplace backend, search, personalization, data engineering |
| [BrowserStack](https://www.browserstack.com/careers) | Test infrastructure, distributed execution, developer tooling |
| [Freshworks](https://www.freshworks.com/company/careers/) | Multi-tenant SaaS, platform services, applied AI |
| [Zoho](https://www.zoho.com/careers/) | SaaS backend, databases, infrastructure engineering |

### Additional employers by engineering focus

**Database engines and AI infrastructure**

| Employer and career page | Suggested search terms |
|---|---|
| [Yugabyte](https://www.yugabyte.com/careers/) | Distributed SQL, PostgreSQL compatibility, replication |
| [PingCAP (TiDB)](https://www.pingcap.com/careers/) | Distributed transactions, query optimization, key-value storage |
| [InfluxData](https://www.influxdata.com/careers/) | Time-series databases, high-throughput ingestion, columnar storage |
| [Dremio](https://www.dremio.com/careers/) | Distributed query execution, Apache Iceberg, lakehouse engines |
| [Tiger Data (Timescale)](https://www.tigerdata.com/careers) | PostgreSQL extensions, time-series analytics, database performance |
| [Pinecone](https://www.pinecone.io/careers/) | Vector indexing, retrieval infrastructure, semantic search |
| [AMD](https://www.amd.com/en/corporate/careers.html) | ROCm, ML compilers, inference optimization |

**Cloud and observability**

| Employer and career page | Suggested search terms |
|---|---|
| [DigitalOcean](https://www.digitalocean.com/careers) | Cloud control plane, Kubernetes, managed databases |
| [NetApp](https://careers.netapp.com/) | Storage systems, replication, cloud data management |
| [Dynatrace](https://www.dynatrace.com/careers/) | Distributed tracing, telemetry pipelines, observability |
| [CrowdStrike](https://www.crowdstrike.com/en-us/careers/) | Event ingestion, detection pipelines, security data platforms |

**Global consumer and payments platforms**

| Employer and career page | Suggested search terms |
|---|---|
| [Booking.com](https://careers.booking.com/) | Marketplace search, experimentation, ranking |
| [Walmart](https://careers.walmart.com/us/en/home) | Global Tech, inventory systems, supply-chain data platforms |
| [Adyen](https://careers.adyen.com/) | Payment processing, ledgers, real-time risk |
| [Canva](https://www.lifeatcanva.com/en/) | Media processing, ML platforms, collaborative editing |
| [DoorDash](https://careersatdoordash.com/) | Dispatch, logistics optimization, experimentation |
| [Pinterest](https://www.pinterestcareers.com/) | Recommendation systems, visual search, feature pipelines |

**Enterprise software and developer tools**

| Employer and career page | Suggested search terms |
|---|---|
| [Postman](https://www.postman.com/company/careers/) | API infrastructure, developer tools, distributed backend services |
| [Druva](https://www.druva.com/why-druva/explore/careers) | Cloud backup, deduplication, distributed storage |
| [Chargebee](https://www.chargebee.com/company/careers/) | Subscription billing, revenue data, payments integrations |
| [Tekion](https://tekion.com/careers) | Automotive SaaS, data platforms, backend services |

### Employers with India compensation benchmarks

Figures are rounded median annual total compensation for software engineers in India across reported levels, checked on 24 November 2026. They include base pay, bonus, and equity where applicable. Reporting samples and seniority mix vary by employer. Compare your own level before using these figures as offer targets.

| Employer and career page | Suggested search terms | Reported median and source |
|---|---|---|
| [Broadcom](https://www.broadcom.com/company/careers) | Virtualization, storage, networking software | [₹1.22 crore](https://www.levels.fyi/companies/broadcom/salaries/software-engineer/locations/india) |
| [Rippling](https://www.rippling.com/careers) | Workflow engines, distributed backend, payroll systems | [₹1.08 crore](https://www.levels.fyi/companies/rippling/salaries/software-engineer/locations/india) |
| [LinkedIn](https://careers.linkedin.com/Teams/india-engineering) | Data infrastructure, search, ranking, recommendation systems | [₹1.00 crore](https://www.levels.fyi/companies/linkedin/salaries/software-engineer/locations/india) |
| [Coinbase](https://www.coinbase.com/careers/positions) | Payments infrastructure, distributed services, data platforms | [₹73.5 lakh](https://www.levels.fyi/companies/coinbase/salaries/software-engineer/locations/india) |
| [Tower Research Capital](https://tower-research.com/open-positions/) | Market data pipelines, low-latency C++, trading infrastructure | [₹69.5 lakh](https://www.levels.fyi/companies/tower-research-capital/salaries/software-engineer/locations/india) |
| [Harness](https://www.harness.io/company/careers) | CI/CD orchestration, cloud infrastructure, developer platforms | [₹63.3 lakh](https://www.levels.fyi/companies/harness/salaries/software-engineer/locations/india) |

## Collecting and sharing matches

1. **Start with one profile.** Record hard requirements such as eligible country separately from preferences such as Python. Keep roles with unclear remote eligibility in a review section. Search full descriptions and titles, including broad titles such as “Member of Technical Staff.” Track pipeline engineering and database-engine development as separate searches.
2. **Seed the watchlist.** Start with 20–30 priority employers. Build Greenhouse and Ashby collection first, then add broad discovery via Adzuna and email alerts. Add newly discovered employers to the watchlist. For the five discovery-only career sites from YC through hirist.tech above, confirm an authorized feed before planning bulk collection.
3. **Handle alert authentication once.** Route saved-search emails into a dedicated mailbox or folder. Authorize mailbox read access with the mail provider. Extract the company, title, location, and link when present. Resolve partial summaries and tracking links to the employer posting where possible. This route requires no ongoing browser session on the job board.
4. **Send each opening once.** For a first personal version, a scheduled Python collector, SQLite, and a daily email suffice. Deduplicate using employer plus requisition ID or canonical application URL. Keep the original source, rank new matches by preferences, and include the direct link and a short reason for each match.
5. **Measure coverage.** Record the last successful fetch and errors per source. Include boards checked, failed fetches, and new matches in the digest. During the first week, compare against manual searches to distinguish missing employers, fetch failures, and overly strict filters. Review source terms before sharing listings publicly.
