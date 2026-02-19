-- Logs Insights query: Count unique active users in a time period
-- Issue #369: CloudWatch Usage Dashboard
-- Usage: Run in CloudWatch Logs Insights console
-- Log group: /aws/lambda/AletheiaAgent, /aws/lambda/AletheiaAuth
--
-- Adjust time range in the console (e.g., last 24 hours, last 7 days)

fields @timestamp, anon_user
| filter action = "request" and ispresent(anon_user)
| stats count_distinct(anon_user) as unique_users,
        count(*) as total_requests
  by bin(1h) as hour
| sort hour desc
