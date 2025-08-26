import ssl

print("Python:", __import__("sys").version.split()[0])
print("OpenSSL:", ssl.OPENSSL_VERSION)
