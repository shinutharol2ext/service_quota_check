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

        self.csv_data = []
    
    def get_active_regions(self):
        try:
            response = self.ec2.describe_regions()
            return [region['RegionName'] for region in response['Regions']]
        except Exception as e:
            print(f"Error getting regions: {e}")
            return ['us-east-1']
    
    def get_quota(self, service_code, quota_code, default_name="Unknown"):
        import time
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
        except Exception as e:
            if 'TooManyRequestsException' in str(e):
                print(f"Rate limited, waiting 2 seconds...")
                time.sleep(2)
                return self.get_quota(service_code, quota_code, default_name)
            elif 'NoSuchResourceException' in str(e):
                print(f"Quota {quota_code} not available for {service_code} in {self.region}")
            else:
                print(f"Warning: Could not fetch quota {quota_code} for {service_code}: {str(e)}")
            quota_info = {'name': default_name, 'value': 'Not available', 'unit': ''}
            self.csv_data.append({
                'Region': self.region,
                'Service': service_code,
                'Quota_Name': default_name,
                'Quota_Code': quota_code,
                'Current_Limit': 'Not available',
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
        
        return quotas
    
    def get_gpu_quotas(self):
        gpu_quotas = {}
        
        gpu_quotas['g4dn_instances'] = self.get_quota('ec2', 'L-DB2E81BA', 'G and VT Spot Instance Requests')
        gpu_quotas['p3_instances'] = self.get_quota('ec2', 'L-417A185B', 'P Spot Instance Requests')
        gpu_quotas['inf1_instances'] = self.get_quota('ec2', 'L-1945791B', 'Inf Spot Instance Requests')
        gpu_quotas['trn1_instances'] = self.get_quota('ec2', 'L-2C3B7624', 'Trn Spot Instance Requests')
        
        return gpu_quotas
    
    
    def print_quota_section(self, title, quotas):
        print(f"{title}:")
        for key, quota in quotas.items():
            name = quota['name'][:50] + "..." if len(quota['name']) > 50 else quota['name']
            print(f"  {name}: {quota['value']} {quota['unit']}")
        print()
    
    def generate_report(self, instance_type=None):
        print(f"=== AWS Service Limits Report ===")
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
        
        if instance_type:
            self.print_quota_section("2. COMPUTE & CAPACITY", self.get_compute_quotas(instance_type))
        self.print_quota_section("3. GPU INSTANCE QUOTAS", self.get_gpu_quotas())
    
        
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

def validate_region(region):
    try:
        ec2 = boto3.client('ec2', region_name='us-east-1')
        response = ec2.describe_regions()
        valid_regions = [r['RegionName'] for r in response['Regions']]
        return region in valid_regions
    except:
        return False

def main():
    parser = argparse.ArgumentParser(description='Check AWS capacity reservations and service quotas')
    parser.add_argument('--region', '-r', help='Specific region to check (default: all regions)')
    parser.add_argument('--instance-type', '-i', help='Instance type to check')
    parser.add_argument('--service', '-s', help='Specific service to check quotas for (e.g., ec2, rds, s3)')
    
    args = parser.parse_args()
    
    # Validate region if provided
    if args.region and not validate_region(args.region):
        print(f"Error: Invalid region '{args.region}'. Please use a valid AWS region.")
        return
    
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
