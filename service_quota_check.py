#!/usr/bin/env python3
import boto3
import json
import argparse
import csv
from datetime import datetime

class CapacityChecker:
    def __init__(self, region='us-east-1'):
        self.region = region
        self.ec2 = boto3.client('ec2', region_name=region)
        self.service_quotas = boto3.client('service-quotas', region_name=region)
        self.elbv2 = boto3.client('elbv2', region_name=region)
        self.rds = boto3.client('rds', region_name=region)
        self.ecs = boto3.client('ecs', region_name=region)
        self.csv_data = []
    
    def get_active_regions(self):
        try:
            response = self.ec2.describe_regions()
            return [region['RegionName'] for region in response['Regions']]
        except Exception as e:
            print(f"Error getting regions: {e}")
            return ['us-east-1']
    
    def get_quota(self, service_code, quota_code, default_name="Unknown"):
        try:
            response = self.service_quotas.get_service_quota(
                ServiceCode=service_code,
                QuotaCode=quota_code
            )
            quota_info = {
                'name': response['Quota']['QuotaName'],
                'value': response['Quota']['Value'],
                'unit': response['Quota']['Unit']
            }
            # Add to CSV data
            self.csv_data.append({
                'Region': self.region,
                'Service': service_code,
                'Quota_Name': quota_info['name'],
                'Quota_Code': quota_code,
                'Current_Limit': quota_info['value'],
                'Unit': quota_info['unit']
            })
            return quota_info
        except:
            quota_info = {'name': default_name, 'value': 'Unable to fetch', 'unit': ''}
            self.csv_data.append({
                'Region': self.region,
                'Service': service_code,
                'Quota_Name': default_name,
                'Quota_Code': quota_code,
                'Current_Limit': 'Unable to fetch',
                'Unit': ''
            })
            return quota_info
    
    def get_capacity_reservations(self):
        try:
            response = self.ec2.describe_capacity_reservations()
            reservations = []
            for cr in response['CapacityReservations']:
                reservation = {
                    'id': cr['CapacityReservationId'],
                    'instance_type': cr['InstanceType'],
                    'instance_count': cr['TotalInstanceCount'],
                    'available_count': cr['AvailableInstanceCount'],
                    'state': cr['State']
                }
                reservations.append(reservation)
                # Add to CSV data
                self.csv_data.append({
                    'Region': self.region,
                    'Service': 'capacity-reservation',
                    'Quota_Name': f"Capacity Reservation - {cr['InstanceType']}",
                    'Quota_Code': cr['CapacityReservationId'],
                    'Current_Limit': f"Total: {cr['TotalInstanceCount']}, Available: {cr['AvailableInstanceCount']}",
                    'Unit': cr['State']
                })
            return reservations
        except Exception as e:
            print(f"Error getting capacity reservations: {e}")
            return []
    
    def get_compute_quotas(self, instance_type):
        family = instance_type.split('.')[0]
        quota_codes = {
            'g4dn': 'L-DB2E81BA', 'g4ad': 'L-DB2E81BA', 'g5': 'L-DB2E81BA', 'g5g': 'L-DB2E81BA',
            'p3': 'L-417A185B', 'p3dn': 'L-417A185B', 'p4d': 'L-417A185B', 'p4de': 'L-417A185B',
            'p5': 'L-417A185B', 'trn1': 'L-2C3B7624', 'trn1n': 'L-2C3B7624', 'inf1': 'L-DB2E81BA',
            'inf2': 'L-DB2E81BA', 'dl1': 'L-6E869C2A',
            'm5': 'L-34B43A08', 'c5': 'L-34B43A08', 'r5': 'L-0E3CBAB9', 't3': 'L-34B43A08'
        }
        
        quotas = {}
        quotas['ec2_instances'] = self.get_quota('ec2', quota_codes.get(family, 'L-34B43A08'))
        quotas['spot_instances'] = self.get_quota('ec2', 'L-34B43A08', 'Spot Instance Requests')
        quotas['dedicated_hosts'] = self.get_quota('ec2', 'L-8B99F1B1', 'Dedicated Hosts')
        
        return quotas
    
    def get_gpu_quotas(self):
        gpu_quotas = {}
        
        gpu_quotas['g4dn_instances'] = self.get_quota('ec2', 'L-DB2E81BA', 'G4DN GPU Instances')
        gpu_quotas['g4ad_instances'] = self.get_quota('ec2', 'L-DB2E81BA', 'G4AD GPU Instances')
        gpu_quotas['g5_instances'] = self.get_quota('ec2', 'L-DB2E81BA', 'G5 GPU Instances')
        gpu_quotas['g5g_instances'] = self.get_quota('ec2', 'L-DB2E81BA', 'G5G GPU Instances')
        
        gpu_quotas['p3_instances'] = self.get_quota('ec2', 'L-417A185B', 'P3 GPU Instances')
        gpu_quotas['p3dn_instances'] = self.get_quota('ec2', 'L-417A185B', 'P3DN GPU Instances')
        gpu_quotas['p4d_instances'] = self.get_quota('ec2', 'L-417A185B', 'P4D GPU Instances')
        gpu_quotas['p4de_instances'] = self.get_quota('ec2', 'L-417A185B', 'P4DE GPU Instances')
        gpu_quotas['p5_instances'] = self.get_quota('ec2', 'L-417A185B', 'P5 GPU Instances')
        
        gpu_quotas['inf1_instances'] = self.get_quota('ec2', 'L-DB2E81BA', 'INF1 Inference Instances')
        gpu_quotas['inf2_instances'] = self.get_quota('ec2', 'L-DB2E81BA', 'INF2 Inference Instances')
        
        gpu_quotas['trn1_instances'] = self.get_quota('ec2', 'L-2C3B7624', 'TRN1 Training Instances')
        gpu_quotas['trn1n_instances'] = self.get_quota('ec2', 'L-2C3B7624', 'TRN1N Training Instances')
        
        gpu_quotas['dl1_instances'] = self.get_quota('ec2', 'L-6E869C2A', 'DL1 Deep Learning Instances')
        
        return gpu_quotas
    
    def get_storage_quotas(self):
        quotas = {}
        quotas['ebs_gp3_storage'] = self.get_quota('ebs', 'L-309BACF6')
        quotas['ebs_io2_iops'] = self.get_quota('ebs', 'L-B3A130E6')
        quotas['ebs_snapshots'] = self.get_quota('ebs', 'L-309BACF6')
        return quotas
    
    def get_networking_quotas(self):
        quotas = {}
        quotas['vpcs_per_region'] = self.get_quota('vpc', 'L-F678F1CE')
        quotas['security_groups_per_vpc'] = self.get_quota('vpc', 'L-E79EC296')
        quotas['elastic_ips'] = self.get_quota('ec2', 'L-0263D0A3')
        quotas['nat_gateways'] = self.get_quota('vpc', 'L-FE5A380F')
        quotas['network_interfaces'] = self.get_quota('vpc', 'L-DF5E4CA3')
        return quotas
    
    def get_load_balancer_quotas(self):
        quotas = {}
        quotas['application_load_balancers'] = self.get_quota('elasticloadbalancing', 'L-53EA0D6D')
        quotas['network_load_balancers'] = self.get_quota('elasticloadbalancing', 'L-69A177A2')
        quotas['targets_per_alb'] = self.get_quota('elasticloadbalancing', 'L-7E6692B2')
        return quotas
    
    def get_dns_quotas(self):
        quotas = {}
        quotas['route53_queries_per_second'] = self.get_quota('route53', 'L-4A133E0D')
        quotas['cloudfront_distributions'] = self.get_quota('cloudfront', 'L-31E22F8E')
        return quotas
    
    def get_monitoring_quotas(self):
        quotas = {}
        quotas['cloudwatch_api_requests'] = self.get_quota('monitoring', 'L-5E141212')
        quotas['cloudwatch_custom_metrics'] = self.get_quota('monitoring', 'L-0E3CBAB9')
        quotas['logs_ingestion_rate'] = self.get_quota('logs', 'L-F7E2A8D9')
        return quotas
    
    def get_database_quotas(self):
        quotas = {}
        quotas['rds_instances'] = self.get_quota('rds', 'L-7B6409FD')
        quotas['rds_read_replicas'] = self.get_quota('rds', 'L-5BC124EF')
        quotas['dynamodb_read_capacity'] = self.get_quota('dynamodb', 'L-1B52F3F2')
        quotas['elasticache_nodes'] = self.get_quota('elasticache', 'L-BCE3B5A8')
        return quotas
    
    def get_container_quotas(self):
        quotas = {}
        quotas['ecs_clusters'] = self.get_quota('ecs', 'L-21C621EB')
        quotas['ecs_services_per_cluster'] = self.get_quota('ecs', 'L-9EF96962')
        quotas['fargate_tasks'] = self.get_quota('fargate', 'L-34B43A08')
        return quotas
    
    def get_security_quotas(self):
        quotas = {}
        quotas['iam_roles'] = self.get_quota('iam', 'L-FE177D64')
        quotas['kms_requests_per_second'] = self.get_quota('kms', 'L-0D7F1F96')
        quotas['secrets_manager_secrets'] = self.get_quota('secretsmanager', 'L-69F38875')
        return quotas
    
    def print_quota_section(self, title, quotas):
        print(f"{title}:")
        for key, quota in quotas.items():
            name = quota['name'][:50] + "..." if len(quota['name']) > 50 else quota['name']
            print(f"  {name}: {quota['value']} {quota['unit']}")
        print()
    
    def generate_report(self, instance_type='g5.2xlarge'):
        print(f"=== AWS Service Limits Report for {instance_type} ===")
        print(f"Region: {self.region}")
        print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        print("1. CAPACITY RESERVATIONS:")
        reservations = self.get_capacity_reservations()
        if reservations:
            for cr in reservations:
                print(f"  ID: {cr['id']} | Type: {cr['instance_type']} | Total: {cr['instance_count']} | Available: {cr['available_count']} | State: {cr['state']}")
        else:
            print("  No capacity reservations found")
        print()
        
        self.print_quota_section("2. COMPUTE & CAPACITY", self.get_compute_quotas(instance_type))
        self.print_quota_section("3. GPU INSTANCE QUOTAS", self.get_gpu_quotas())
        self.print_quota_section("4. STORAGE LIMITS", self.get_storage_quotas())
        self.print_quota_section("5. NETWORKING LIMITS", self.get_networking_quotas())
        self.print_quota_section("6. LOAD BALANCER LIMITS", self.get_load_balancer_quotas())
        self.print_quota_section("7. DNS & TRAFFIC LIMITS", self.get_dns_quotas())
        self.print_quota_section("8. MONITORING LIMITS", self.get_monitoring_quotas())
        self.print_quota_section("9. DATABASE LIMITS", self.get_database_quotas())
        self.print_quota_section("10. CONTAINER LIMITS", self.get_container_quotas())
        self.print_quota_section("11. SECURITY LIMITS", self.get_security_quotas())
        
        print("=== CRITICAL PRE-EVENT ACTIONS ===")
        print("1. Request quota increases 2-3 weeks in advance")
        print("2. Test scaling scenarios in non-production")
        print("3. Set up monitoring dashboards for real-time tracking")
        print("4. Configure CloudWatch alarms for quota thresholds")
        print("5. Prepare rollback procedures for capacity issues")
        print("6. Coordinate with AWS TAM/Support for large events")
        print("7. Use AWS Trusted Advisor for limit monitoring")
        print("8. Consider multi-region deployment for redundancy")
        print()
        
        print("=== EVENT DAY MONITORING ===")
        print("- Monitor service health dashboards")
        print("- Track quota utilization in real-time")
        print("- Have escalation procedures ready")
        print("- Monitor application performance metrics")
        print()
        
        print("=== IMPORTANT NOTE ===")
        print("Review all quotas above and submit quota increase requests if necessary")
        print("to address your upcoming event. Allow 24-48 hours for quota increases.")
        print("Use AWS Service Quotas console or AWS CLI to request increases.")

def write_csv_report(all_csv_data, timestamp):
    filename = f"service_quota_check_{timestamp}.csv"
    
    with open(filename, 'w', newline='') as csvfile:
        fieldnames = ['Region', 'Service', 'Quota_Name', 'Quota_Code', 'Current_Limit', 'Unit']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        for row in all_csv_data:
            writer.writerow(row)
    
    print(f"\nCSV report saved as: {filename}")
    return filename

def main():
    parser = argparse.ArgumentParser(description='Check AWS capacity reservations and service quotas')
    parser.add_argument('--region', '-r', help='Specific region to check (default: all regions)')
    parser.add_argument('--instance-type', '-i', default='g5.2xlarge', help='Instance type to check (default: g5.2xlarge)')
    
    args = parser.parse_args()
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    all_csv_data = []
    
    if args.region:
        print(f"Checking region: {args.region}\n")
        try:
            checker = CapacityChecker(region=args.region)
            checker.generate_report(args.instance_type)
            all_csv_data.extend(checker.csv_data)
        except Exception as e:
            print(f"Error checking region {args.region}: {e}")
    else:
        initial_checker = CapacityChecker(region='us-east-1')
        regions = initial_checker.get_active_regions()
        
        print(f"Checking {len(regions)} regions...\n")
        
        for region in regions:
            print(f"{'='*60}")
            print(f"REGION: {region.upper()}")
            print(f"{'='*60}")
            
            try:
                checker = CapacityChecker(region=region)
                checker.generate_report(args.instance_type)
                all_csv_data.extend(checker.csv_data)
            except Exception as e:
                print(f"Error checking region {region}: {e}")
            
            print("\n")
    
    # Write CSV report
    write_csv_report(all_csv_data, timestamp)

if __name__ == "__main__":
    main()
