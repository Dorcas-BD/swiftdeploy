package infrastructure

import rego.v1

default allow := false

deny contains msg if {
    input.disk_free_gb < data.thresholds.disk_free_min_gb
    msg := sprintf("Disk free space is %dGB, minimum required is %dGB", [input.disk_free_gb, data.thresholds.disk_free_min_gb])
}

deny contains msg if {
    input.cpu_load > data.thresholds.cpu_load_max
    msg := sprintf("CPU load is %.2f, maximum allowed is %.1f", [input.cpu_load, data.thresholds.cpu_load_max])
}

allow if {
    count(deny) == 0
}
