#!/bin/bash

# Create test directories if they don't exist
mkdir -p teste
mkdir -p vizinhos

# Create test files
dd if=/dev/urandom of=teste/1KB.txt bs=1K count=1
dd if=/dev/urandom of=teste/10KB.txt bs=1K count=10
dd if=/dev/urandom of=teste/100KB.txt bs=1K count=100

# Create neighbor configuration files
echo "127.0.0.1:8002
127.0.0.1:8004" > vizinhos/v1_vizinhos.txt

echo "127.0.0.1:8001
127.0.0.1:8004" > vizinhos/v2_vizinhos.txt

echo "127.0.0.1:8001
127.0.0.1:8002" > vizinhos/v4_vizinhos.txt