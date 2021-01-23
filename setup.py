import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    version                       = "0.5.1"         ,               # change this on every release
    name                          = "osbot_docker"  ,
    author                        = "Dinis Cruz"    ,
    author_email                  = "dinis.cruz@owasp.org",
    description                   = "OWASP Security Bot - Docker",
    long_description              = long_description,
    long_description_content_type = "text/markdown",
    url                           = "https://github.com/owasp-sbot/OSBot-Docker",
    packages                      = setuptools.find_packages(),
    classifiers                   = [ "Programming Language :: Python :: 3"   ,
                                      "License :: OSI Approved :: MIT License",
                                      "Operating System :: OS Independent"   ])
