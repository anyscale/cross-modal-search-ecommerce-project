calc-embeddings-local:
	pip install -e .
	pip install -r embeddings/requirements.txt
	python embeddings/main.py --mode img --model-name openai

calc-embeddings-anyscale:
	cp -rp . /mnt/cluster_storage/demo-anyscale/
	pip install -e /mnt/cluster_storage/demo-anyscale
	pip install -r embeddings/requirements.txt
	python embeddings/main.py --mode img --model-name openai

install-inference-reqs:
	pip install -r inference/requirements.txt

service-backend: install-inference-reqs
	serve run inference.backend:app --non-blocking

deploy-backend: install-inference-reqs
	serve deploy -f inference/backend_config.yaml

deploy-frontend: install-inference-reqs
	serve deploy -f inference/frontend_config.yaml
	
deploy-app: install-inference-reqs
	serve deploy -f inference/inference_config.yaml

test-txt:
	curl -X POST http://localhost:8000/text_search \
	-H 'Content-Type: application/json' \
	-d '{"query": "a man in a blue shirt", "model": "patrickjohncyh/fashion-clip", "num_results": "5"}'

shutdown:
	serve shutdown

frontend-pascal:
	docker compose up frontend --build

anyscale-job-embeddings:
	anyscale job submit embeddings/job.yaml --follow --name calc-embeddings