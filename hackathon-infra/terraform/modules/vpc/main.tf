#------------------------------------------------------------------------------
# VPC
#------------------------------------------------------------------------------
resource "aws_vpc" "main" {
  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-vpc"
  })
}

#------------------------------------------------------------------------------
# Internet Gateway
#------------------------------------------------------------------------------
resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-igw"
  })
}

#------------------------------------------------------------------------------
# Public Subnets
#------------------------------------------------------------------------------
resource "aws_subnet" "public" {
  count = length(var.public_subnet_cidrs)

  vpc_id                  = aws_vpc.main.id
  cidr_block              = var.public_subnet_cidrs[count.index]
  availability_zone       = var.availability_zones[count.index]
  map_public_ip_on_launch = true

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-public-${count.index + 1}"
    Tier = "public"
  })
}

#------------------------------------------------------------------------------
# Route Table
#------------------------------------------------------------------------------
resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main.id
  }

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-public-rtb"
  })
}

resource "aws_route_table_association" "public" {
  count = length(aws_subnet.public)

  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public.id
}

#------------------------------------------------------------------------------
# Elastic IPs for LiveKit, Coturn, and Jitsi
#------------------------------------------------------------------------------
# PROTECTION: EIPs have DNS records pointing to them and are limited (8 per region).
# Accidental deletion causes DNS propagation delays and potential quota issues.
# To destroy: first set prevent_destroy = false, then run terraform apply, then destroy.

resource "aws_eip" "livekit" {
  domain = "vpc"

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-livekit-eip"
  })

  lifecycle {
    prevent_destroy = true
  }
}

resource "aws_eip" "coturn" {
  domain = "vpc"

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-coturn-eip"
  })

  lifecycle {
    prevent_destroy = true
  }
}

resource "aws_eip" "jitsi" {
  domain = "vpc"

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-jitsi-eip"
  })

  lifecycle {
    prevent_destroy = true
  }
}
