# -----------------------------------------------------------------------------
# Outputs
# -----------------------------------------------------------------------------

output "instance_name" {
  description = "Name of the vLLM server instance"
  value       = google_compute_instance.vllm_server.name
}

output "instance_zone" {
  description = "Zone where the instance is deployed"
  value       = google_compute_instance.vllm_server.zone
}

output "external_ip" {
  description = "External IP address of the vLLM server"
  value       = google_compute_instance.vllm_server.network_interface[0].access_config[0].nat_ip
}

output "vllm_api_endpoint" {
  description = "vLLM API endpoint URL"
  value       = "http://${google_compute_instance.vllm_server.network_interface[0].access_config[0].nat_ip}:8000"
}

output "vllm_health_endpoint" {
  description = "vLLM health check URL"
  value       = "http://${google_compute_instance.vllm_server.network_interface[0].access_config[0].nat_ip}:8000/health"
}

output "ssh_command" {
  description = "SSH command to connect to the instance"
  value       = "gcloud compute ssh ${google_compute_instance.vllm_server.name} --zone=${google_compute_instance.vllm_server.zone} --project=${var.project_id}"
}

output "stop_command" {
  description = "Command to stop the instance (save costs)"
  value       = "gcloud compute instances stop ${google_compute_instance.vllm_server.name} --zone=${google_compute_instance.vllm_server.zone} --project=${var.project_id}"
}

output "start_command" {
  description = "Command to start the instance"
  value       = "gcloud compute instances start ${google_compute_instance.vllm_server.name} --zone=${google_compute_instance.vllm_server.zone} --project=${var.project_id}"
}

output "logs_command" {
  description = "Command to view vLLM container logs"
  value       = "gcloud compute ssh ${google_compute_instance.vllm_server.name} --zone=${google_compute_instance.vllm_server.zone} --project=${var.project_id} --command='docker logs -f kanoa-vllm'"
}

output "estimated_hourly_cost" {
  description = "Estimated hourly cost (USD) - L4 GPU in us-central1"
  value       = "~$0.70/hr (g2-standard-8 with L4 GPU)"
}
