package canary

import rego.v1

default allow := false

deny contains msg if {
    input.error_rate > data.thresholds.error_rate_max
    msg := sprintf("Error rate %.4f exceeds maximum allowed %.4f", [input.error_rate, data.thresholds.error_rate_max])
}

deny contains msg if {
    input.p99_latency_ms > data.thresholds.p99_latency_max_ms
    msg := sprintf("P99 latency is %vms, maximum allowed is %vms", [input.p99_latency_ms, data.thresholds.p99_latency_max_ms])
}

allow if {
    count(deny) == 0
}
