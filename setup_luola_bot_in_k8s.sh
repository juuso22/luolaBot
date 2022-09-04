kubectl create secret generic luola-bot-config --from-file=luolabot.yaml
sed s+{{pwd}}+$(pwd)+ luola-bot-manifest-template.yaml | tee luola-bot-manifest.yaml 
kubectl apply -f statefulset-luolabot.yaml
