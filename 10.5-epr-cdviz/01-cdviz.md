# CDViz: Visualizing CI/CD Events

## Environment Setup

### Clone and Launch CDViz

**Objective:** Get the CDViz demo environment running locally

Clone the repository

```bash
mkdir ./src
cd ./src
git clone https://github.com/cdviz-dev/cdviz.git
```

Start Backend Services

```bash
cd ./src/cdviz/demos/stack-compose
```

Launch the docker compose demo (in foreground)

```bash
docker compose -f docker-compose.yaml pull
docker compose -f docker-compose.yaml up --remove-orphans
```

---

Verify the services are running:

```bash
docker compose ps
```

Access the demo dashboard:

Open
[http://localhost:3000/d/demo_service_deployed/service3a-demo](http://localhost:3000/d/demo_service_deployed/service3a-demo)

**Expected Outcome:** You should see a Grafana dashboard with initial sample
data showing deployment metrics.

**Troubleshooting Tips:**

- If ports are in use, check for existing Docker containers
- Ensure Docker Desktop is running
- Wait a few minutes for all services to fully initialize

---

### Explore the Initial Dashboard

**Objective:** Understand the default CDViz dashboard components

Examine the dashboard panels:

- Deployment Frequency chart
- Deployed Services list
- Incidents Reported section

Note the time range selector in the top-right corner

Check the data source by looking at the sample events

---

## Sending Events via Web Interface

### Create Service Deployment Events

**Objective:** Learn to send service deployment events through the web form

Scroll down to the "Services Deployed" form

Fill out the form with the following sample data:

- **Service Name:** `user-authentication-service`
- **Environment:** `production`
- **Version:** `v2.1.0`
- **Artifact:** `pkg:oci/user-auth@sha256:a1b2c3d4e5f6789012345`

Submit the form

Observe the dashboard updates:

- Check the Deployment Frequency chart
- Look for your service in the Deployed Services panel

Send 2-3 more deployment events with different services:

- `payment-processor` (v1.5.2, staging)
- `notification-service` (v3.0.1, production)

Hands-on Challenge:

Create a deployment event for a service in your organization. Use realistic
names and version numbers.

---

### Report Incidents

**Objective:** Practice incident reporting and observe impact on metrics

1. **Locate the "Incidents Reported" form**

2. **Create an incident with these details:**

   - **Service:** `user-authentication-service`
   - **Severity:** `High`
   - **Description:** `Login failures due to database timeout`
   - **Status:** `Open`

3. **Submit and observe the dashboard changes**

4. **Create a follow-up incident resolution:**
   - Same service
   - Status: `Resolved`
   - Description: `Database connection pool increased, issue resolved`

**Discussion:** How do incidents relate to deployments in the dashboard? What
patterns can you identify?

---

### Advanced Event Submission

**Objective:** Use the raw JSON form to send complex events

**Steps:**

1. **Find the "Raw JSON" form at the bottom of the page**

2. **Submit this CD Event JSON:**

   ```json
   {
     "context": {
       "version": "0.4.1",
       "source": "jenkins.company.com",
       "type": "dev.cdevents.service.deployed.0.1.4",
       "timestamp": "2025-09-18T10:30:00Z"
     },
     "subject": {
       "id": "api-gateway/production",
       "type": "service",
       "content": {
         "artifactId": "pkg:docker/api-gateway@v1.2.3",
         "environment": "production"
       }
     }
   }
   ```

3. **Verify the event appears in the dashboard**

**Challenge:** Modify the JSON to create a test environment deployment with your
own service details.

---

### Simulate Different Event Types

**Objective:** Understand various CD Event types

**Create workflow steps for different scenarios:**

1. **Build Started Event:**

   ```json
   {
     "context": {
       "version": "0.4.1",
       "source": "github.com/${{ github.repository }}",
       "type": "dev.cdevents.build.started.0.1.0"
     },
     "subject": {
       "id": "${{ github.run_id }}",
       "type": "build"
     }
   }
   ```

---

2. **Test Completed Event:**
   ```json
   {
     "context": {
       "version": "0.4.1",
       "source": "github.com/${{ github.repository }}",
       "type": "dev.cdevents.test.completed.0.1.0"
     },
     "subject": {
       "id": "${{ github.run_id }}-tests",
       "type": "test",
       "content": {
         "outcome": "success"
       }
     }
   }
   ```

---

## Dashboard Exploration and Customization

### Explore the CDEvents Activity Dashboard

**Objective:** Understand detailed event tracking

**Steps:**

1. **Navigate to the CDEvents Activity dashboard:**
   [http://localhost:3000/d/cdevents-activity/cdevents-activity](http://localhost:3000/d/cdevents-activity/cdevents-activity)

2. **Explore the different panels:**

   - Event timeline
   - Event types distribution
   - Source systems breakdown

3. **Filter events by:**

   - Time range (last 1 hour, 6 hours, 1 day)
   - Event type
   - Source system

4. **Identify patterns in your submitted events**

**Analysis Questions:**

- Which services are deployed most frequently?
- What's the ratio of successful to failed events?
- Are there any time-based patterns?

---

### Create a Custom Dashboard

**Objective:** Build a dashboard tailored to specific needs

**Steps:**

1. **Access Grafana's dashboard creation:**

   - Go to the "+" icon > "Dashboard"
   - Click "Add a new panel"

2. **Create a deployment frequency panel:**

   - Data source: Select the CDViz database
   - Query: Count deployments by service
   - Visualization: Bar chart
   - Title: "Deployments by Service (Last 24h)"

3. **Add a second panel for environment breakdown:**

   - Query: Group deployments by environment
   - Visualization: Pie chart
   - Title: "Deployment Distribution by Environment"

4. **Save your dashboard** as "My CDViz Dashboard"

**Challenge:** Add a panel showing the time between deployments (deployment
cadence) for each service.

---

### Set Up Alerts

**Objective:** Create proactive monitoring with alerts

**Steps:**

1. **Create an alert rule:**

   - Go to "Alerting" > "Alert rules"
   - Create a new rule for high incident frequency
   - Condition: More than 3 incidents in 1 hour

2. **Configure notification channels:**

   - Set up email or Slack notification (simulation)
   - Test the alert system

3. **Create a second alert:**
   - Zero deployments in production for 8 hours
   - Could indicate deployment pipeline issues

**Discussion:** What other alerts would be valuable for your organization's
CI/CD monitoring?

---

## Real-World Integration Scenarios

### Multi-Tool Integration Planning

**Objective:** Design CDViz integration for a realistic CI/CD pipeline

**Scenario Planning Exercise:**

1. **Your Current Stack:**

   - Version Control: GitHub/GitLab
   - CI/CD: Jenkins/GitHub Actions/GitLab CI
   - Deployment: Kubernetes/Docker
   - Monitoring: Prometheus/Grafana
   - Issue Tracking: Jira/GitHub Issues

2. **Integration Points Identification:**

   - Where would you send deployment events?
   - How would you capture test results?
   - When would incidents be automatically created?

3. **Design Your Event Flow:** Draw a diagram showing:
   - Event sources
   - CDViz collector endpoints
   - Dashboard consumers

---

### Event Schema Design

**Objective:** Plan standardized events for your organization

**Steps:**

1. **Define your service taxonomy:**

   - Service naming conventions
   - Environment definitions (dev, staging, prod, etc.)
   - Version numbering scheme

2. **Create standard event templates:**

   ```json
   {
     "context": {
       "version": "0.4.1",
       "source": "your-ci-system",
       "type": "dev.cdevents.service.deployed.0.1.4"
     },
     "subject": {
       "id": "{service-name}/{environment}",
       "type": "service",
       "content": {
         "artifactId": "pkg:docker/{service-name}@{version}",
         "environment": "{environment}",
         "deploymentId": "{deployment-id}",
         "team": "{owning-team}"
       }
     }
   }
   ```

3. **Document your standards:**
   - Required vs. optional fields
   - Validation rules
   - Naming conventions

---

## Performance and Troubleshooting (20 minutes)

### Load Testing

**Objective:** Understand CDViz performance characteristics

**Steps:**

1. **Create a simple load test script:**

   ```bash
   #!/bin/bash
   for i in {1..50}; do
     curl -X POST http://localhost:8080/webhook/github-actions \
       -H "Content-Type: application/json" \
       -d '{
         "context": {
           "version": "0.4.1",
           "source": "load-test",
           "type": "dev.cdevents.service.deployed.0.1.4"
         },
         "subject": {
           "id": "test-service-'$i'/production",
           "type": "service"
         }
       }'
     sleep 0.1
   done
   ```

2. **Monitor dashboard performance:**

   - Refresh rate
   - Query execution time
   - Memory usage

3. **Check the Docker container logs:**
   ```bash
   docker compose logs cdviz-collector
   docker compose logs cdviz-db
   ```

---

### Common Issues Resolution

**Troubleshooting Practice:**

1. **Simulate event validation errors:**

   - Send malformed JSON
   - Use invalid event types
   - Observe error responses and logs

2. **Database connectivity issues:**

   - Stop the database container
   - Observe collector behavior
   - Restart and verify recovery

3. **Dashboard performance:**
   - Identify slow-loading panels
   - Optimize queries
   - Implement appropriate time ranges

---

## Workshop Wrap-up

### Key Takeaways

**Technical Skills Acquired:**

- CDViz platform setup and configuration
- Multiple methods of event submission
- Dashboard creation and customization
- Integration with CI/CD workflows

**Monitoring Concepts:**

- Deployment frequency metrics
- Incident correlation with deployments
- Lead time and cycle time tracking
- Alert-based proactive monitoring

---

### Next Steps for Your Organization

1. **Assessment Phase:**

   - Inventory your current CI/CD tools
   - Identify integration points
   - Define success metrics

2. **Pilot Implementation:**

   - Start with one team or service
   - Implement basic deployment tracking
   - Create essential dashboards

3. **Scaling Strategy:**
   - Standardize event schemas
   - Automate integration across teams
   - Establish governance processes

### Resources for Continued Learning

- **CDViz Documentation:** https://cdviz.dev/docs/
- **CD Events Specification:** https://cdevents.dev/
- **Grafana Documentation:** https://grafana.com/docs/
- **DORA Metrics:** Research and best practices

---

### Workshop Feedback

**Reflection Questions:**

1. What was the most valuable part of this workshop?
2. Which integration scenario is most relevant to your work?
3. What additional features would you want to see in CDViz?
4. How would you present CDViz benefits to your team/organization?

---

## Appendix: Quick Reference

### Useful Commands

```bash
# Start CDViz
docker compose up -d

# View logs
docker compose logs -f cdviz-collector

# Stop CDViz
docker compose down

# Reset data
docker compose down -v
docker compose up -d
```

---

### Sample Event Templates

```json
// Deployment Event
{
  "context": {
    "version": "0.4.1",
    "source": "your-system",
    "type": "dev.cdevents.service.deployed.0.1.4"
  },
  "subject": {
    "id": "service/environment",
    "type": "service"
  }
}

// Test Event
{
  "context": {
    "version": "0.4.1",
    "source": "your-system",
    "type": "dev.cdevents.test.completed.0.1.0"
  },
  "subject": {
    "id": "test-run-123",
    "type": "test",
    "content": {
      "outcome": "success"
    }
  }
}
```

### Common URLs

- Main Dashboard:
  http://localhost:3000/d/demo-service-deployed/demo-service-deployed
- Activity Dashboard:
  http://localhost:3000/d/cdevents-activity/cdevents-activity
- Event Webhook: http://localhost:8080/webhook/github-actions

---

## Post CDEvents

```bash
curl -v -X POST http://localhost:8080/webhook/000-cdevents \
    -H "Content-Type: application/json" \
    -d @01K5S8WZ0WQBK64MJNNVX2SW8Y.example.deployed.json
```

---

## Scripts

Copy the `generate_cdevents.py` script into a work directory.

```bash
mkdir -p ./src/work
cp -v ../../src/{generate_cdevents.py,requirements.txt} .
```

Create a virtual env with requirements and activate.

```bash
python3 -m venv ./venv/cdviz
source ./venv/cdviz/bin/activate
pip install -r requirements.txt
```

Generate CDViz content

```bash
python3 ./generate_cdevents.py
```

Look at the dashboard to see the events.

---
