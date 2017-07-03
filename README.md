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
It includes one main stage: Function Test. It runs Function Test against RackHD source code.

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
