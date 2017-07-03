# on-build-config 

'on-build-config' is the repository for RackHD CI/CD pipelines.
Currently, there are 4 pipelines: 
- [MasterCI](http://147.178.202.18/job/MasterCI/)  
- [ContinuousFunctionTest](http://147.178.202.18/job/ContinuousFunctionTest/)
- [PR Gate](http://147.178.202.18/job/RackHD/)
- [SprintRelease](http://147.178.202.18/job/SprintRelease/) 

Copyright 2017, DELLEMC, Inc.

## MasterCI

*The entry point of MasterCI: jobs/MasterCI/MasterCI*

The pipeline is responsible for RackHD daily release.
It includes below 6 main stages:
1. Unit Test: run unit test for each repository of RackHD
2. Function Test: run Function Test against RackHD source code
3. Packages Build: build debian packages of RackHD
4. Images Build: build ova, vagrant, docker images of RackHD
5. Post Test: run Function Test against built iamges
6. Publish: push package and images to public platform
   - debian packages -> [bintray](https://bintray.com/rackhd/debian)
   - npm packges -> [npm registry](https://www.npmjs.com/~rackhd)
   - vagrant box -> [atlas](https://app.vagrantup.com/rackhd/boxes/rackhd)
   - docker images -> [docker hub](https://hub.docker.com/u/rackhd/)

## ContinuousFunctionTest

*The entry point of ContinuousFunctionTest: jobs/ContinuousTest/Jenkinsfile*

The pipeline is responsible for testing the stability of RackHD.

1.It includes one main stage: Function Test. It runs Function Test against RackHD source code.

2.If you want to run the Function Test locally, follow below steps:

   a. Setup test environment

       wget https://raw.githubusercontent.com/RackHD/on-build-config/master/deploy_ci_locally/deploy_ci_locally.sh
       # The script does below steps:
       # 1. Clean up environment, such as stopping previous running containers, service mongodb and rabbitmq-server
       # 2. Checkout RackHD source code and run "npm install" under each repository of RackHD
       # 3. Download static files and docker base image
       # 4. Update config file under RackHD/test/config with IP of NIC whose ip starts with 172.31.128
       # 5. Build a docker image which contains RackHD and its dependents
       # 6. Run the build docker image
       # 7. Create the virtual env for test

       # Get help of the script
       ./deploy_ci_locally.sh -h
       # Deploy ci envitonment
       ./deploy_ci_locally.sh deploy -w workspace -p password
       # Cleanup
       ./deploy_ci_locally.sh cleanUp -p password


   b. Deploy virtual Nodes or physical Nodes

   c. Run test with stack "docker_local_run" (Doc for test: https://github.com/RackHD/RackHD/blob/master/test/README.md)

       # Go to RackHD directory ( If you didn't provide the argument  --RACKHD_DIR(RackHD directory) at step (a) above, RackHD will be clone by default in $WORKSPACE/RackHD/ )
       cd $WORKSPACE/RackHD/test

       #activate virtualenv (it was created in deploy_ci_locally.sh)
       source myenv_on-build-config

       # Run test with script run_tests.py
       # Arguments:
       # -test: Directory of test script
       # -group: target test group, such as smoke
       # -stack: target test stack, such as docker_local_run
       # --sm-amqp-use-user: user for accessing amqp
       # -xunit: generate xunit report
       # -v: Verbosity level of console and log output, 0~9, 0: Minimal logging; 9: Display infra.* and test.* at DEBUG_9 (max output)
       # -extra: comma separated list of extra config files (found in 'config' directory)

       # Run stack init
       python run_tests.py -test deploy/rackhd_stack_init.py -stack docker_local_run --sm-amqp-use-user guest -xunit

       # Run smoke test
       python run_tests.py -test tests -group smoke -stack docker_local_run --sm-amqp-use-user guest -v 4 -xunit

       # Test Install Centos 6.5
       python run_tests.py -test tests/bootstrap/test_api20_linux_bootstrap.py -extra install_centos65_minimum.json -stack docker_local_run --sm-amqp-use-user guest -v 4 -xunit

       # Test Install ESXi 6.0
       python run_tests.py -test tests/bootstrap/test_api20_esxi_bootstrap.py -extra install_esxi6.0_minimum.json -stack docker_local_run --sm-amqp-use-user guest -v 4 -xunit

       # Test Install Ubuntu 14.04
       python run_tests.py -test tests/bootstrap/test_api20_linux_bootstrap.py -extra install_ubuntu14.04_minimum.json -stack docker_local_run --sm-amqp-use-user guest -v 4 -xunit



## PR Gate
*The entry point of PR Gate: jobs/pr_gate/Jenkinsfile*

The pipeline is responsible for testing each pull request of RackHD.
Each pull request of each repository of RackHD will trigger the building of the pipeline.
It includes 2 main stages: 
1. Unit Test: run Unit Test of repositories which are impacted by the pull request.
2. Function Test: run Function Test against RackHD source code with the pull request.


## SprintRelease
*The entry point of SprintRelease: jobs/SprintRelease/Jenkinsfile*

The pipeline is responsible for RackHD sprint release(1 week a sprint).
It includes below 6 main stages:
1. Unit Test: run unit test for each repository of RackHD
2. Function Test: run Function Test against RackHD source code
3. Packages Build: build debian packages of RackHD
4. Images Build: build ova, vagrant, docker images of RackHD
5. Post Test: run Function Test against built iamges
6. Publish: push package and images to public platform
   - debian packages -> [bintray](https://bintray.com/rackhd/debian)
   - npm packges -> [npm registry](https://www.npmjs.com/~rackhd)
   - vagrant box -> [atlas](https://app.vagrantup.com/rackhd/boxes/rackhd)
   - docker images -> [docker hub](https://hub.docker.com/u/rackhd/)
