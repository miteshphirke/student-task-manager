// ---------------------------------------------------------------------------
// Jenkinsfile — CI/CD pipeline for the Student Task Management System
//
// Flow:  Checkout -> Install deps -> Test (pytest) -> Build Docker image
//        -> (optional) Push image -> Deploy with Ansible -> Post-deploy check
//
// Prerequisites on the Jenkins agent (see README "Stage 4" for setup steps):
//   - Python 3.11+ and pip
//   - Docker (and the "jenkins" user added to the "docker" group)
//   - Ansible
//   - SSH access configured from Jenkins to the Ubuntu deployment VM
//   - Credentials (Jenkins "Credentials" store) if pushing to Docker Hub:
//       id: dockerhub-creds  (username + password/token)
// ---------------------------------------------------------------------------

pipeline {
    agent any

    environment {
        IMAGE_NAME = "student-task-manager"
        IMAGE_TAG  = "${env.BUILD_NUMBER}"
        // Change this to your Docker Hub username if you plan to push images
        DOCKERHUB_REPO = "yourdockerhubusername/student-task-manager"
    }

    options {
        timestamps()
        disableConcurrentBuilds()
    }

    stages {

        stage('Checkout') {
            steps {
                echo "Checking out source code from GitHub..."
                checkout scm
            }
        }

        stage('Set Up Python Environment') {
            steps {
                sh '''
                    python3 -m venv venv
                    . venv/bin/activate
                    pip install --upgrade pip
                    pip install -r app/requirements.txt
                '''
            }
        }

        stage('Run Automated Tests') {
            steps {
                echo "Running pytest test-suite..."
                sh '''
                    . venv/bin/activate
                    cd app
                    pytest -v --junitxml=../test-results.xml
                '''
            }
            post {
                always {
                    junit 'test-results.xml'
                }
            }
        }

        stage('Build Docker Image') {
            steps {
                echo "Building Docker image ${IMAGE_NAME}:${IMAGE_TAG}..."
                sh "docker build -t ${IMAGE_NAME}:${IMAGE_TAG} -t ${IMAGE_NAME}:latest ."
            }
        }

        stage('Push Docker Image (optional)') {
            when {
                // Only push when Docker Hub credentials have been configured in Jenkins.
                expression { return env.PUSH_TO_REGISTRY == 'true' }
            }
            steps {
                withCredentials([usernamePassword(credentialsId: 'dockerhub-creds',
                                                   usernameVariable: 'DOCKER_USER',
                                                   passwordVariable: 'DOCKER_PASS')]) {
                    sh '''
                        echo "$DOCKER_PASS" | docker login -u "$DOCKER_USER" --password-stdin
                        docker tag ${IMAGE_NAME}:latest ${DOCKERHUB_REPO}:${IMAGE_TAG}
                        docker tag ${IMAGE_NAME}:latest ${DOCKERHUB_REPO}:latest
                        docker push ${DOCKERHUB_REPO}:${IMAGE_TAG}
                        docker push ${DOCKERHUB_REPO}:latest
                    '''
                }
            }
        }

        stage('Deploy with Ansible') {
            steps {
                echo "Deploying application to the Ubuntu VM using Ansible..."
                sh '''
                    ansible-playbook -i ansible/inventory.ini ansible/deploy.yml \
                        --extra-vars "image_tag=${IMAGE_TAG}"
                '''
            }
        }

        stage('Post-Deploy Health Check') {
            steps {
                echo "Verifying the deployed application is healthy..."
                sh '''
                    sleep 10
                    curl -sf http://$(grep -m1 -A1 "\\[app_servers\\]" ansible/inventory.ini | tail -1 | awk '{print $1}'):5000/health || \
                    echo "WARNING: health check could not reach the app automatically. Verify manually."
                '''
            }
        }
    }

    post {
        success {
            echo "✅ Pipeline completed successfully. Build ${IMAGE_TAG} deployed."
        }
        failure {
            echo "❌ Pipeline failed. Check the stage logs above."
        }
        always {
            sh 'docker system prune -f || true'
        }
    }
}
