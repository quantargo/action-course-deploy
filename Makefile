R := R --slave -e
RMD_FILES := $(shell find 0* -type f -maxdepth 1 -name '*.Rmd')
OUT_JSON := $(RMD_FILES:.Rmd=.json)
OUT_PNG := $(RMD_FILES:.Rmd=.png)
OUT_PNG_COURSE := main/course_og.png
OUT_QBIT := "qbit-$(SLUG)"

ifeq "$(STAGE)" "prod"
    S3_BUCKET_ASSETS := s3://www-quantargo-app-client/assets
else
    S3_BUCKET_ASSETS := s3://www-quantargo-app-client-next/assets
endif

CHAPTER_DIRS := $(shell find . -maxdepth 1 -mindepth 1 -type d -name '[0-9]*' | cut -c 3-)
.PHONY: all json clean deploy deploy-qbit index

all: json index

json: $(OUT_JSON)

images: ${OUT_PNG}
	$(R) 'qlearn::course_main_image()'

clean:
	find . -type f -name *.html -exec rm {} +
	find . -type f -name *.json -exec rm {} +
	rm -rf $(OUT_QBIT)
	find . -type d -name *_files -exec rm -r {} +
	find . -type d -name *_cache -exec rm -r {} +
	find . -type d -name *.html_cache -exec rm -r {} +
	rm $(OUT_PNG) $(OUT_PNG_COURSE)

deploy-qbit:
	$(R) 'library(qbit); deploy(sprintf("qbit-%s", "$(SLUG)"), meta = list(type="course"))'

deploy: $(OUT_JSON) $(OUT_ASSETS) index deploy-qbit
	python3 script_upload_dynamodb.py $(OUT_JSON)
	for cdir in $(CHAPTER_DIRS) ; do \
    aws s3 sync $$cdir $(S3_BUCKET_ASSETS)/courses/$(SLUG)/$$cdir --delete --exclude "*.html" --exclude "*.Rmd" --exclude "*.json" --exclude ".DS_Store"; \
	done
	aws s3 sync main $(S3_BUCKET_ASSETS)/courses/$(SLUG)/main --delete --exclude "*.html" --exclude "*.Rmd" --exclude "*.json" --exclude ".DS_Store"
	mkdir -p $(OUT_QBIT)
	aws s3 sync $(OUT_QBIT) $(S3_BUCKET_ASSETS)/qbits/$(OUT_QBIT) --delete --exclude ".DS_Store"

deploy-no-qbit: $(OUT_JSON) $(OUT_ASSETS) index
	python3 script_upload_dynamodb.py $(OUT_JSON)
	for cdir in $(CHAPTER_DIRS) ; do \
    aws s3 sync $$cdir $(S3_BUCKET_ASSETS)/courses/$(SLUG)/$$cdir --delete --exclude "*.html" --exclude "*.Rmd" --exclude "*.json" --exclude ".DS_Store"; \
	done
	aws s3 sync main $(S3_BUCKET_ASSETS)/courses/$(SLUG)/main --delete --exclude "*.html" --exclude "*.Rmd" --exclude "*.json" --exclude ".DS_Store"

index: $(OUT_JSON)
	python3 script_create_index.py

%.json : %.Rmd
	$(R) 'library(qlearn); rmarkdown::render("$<", output_format = "qlearn::qlearn")'

%.png : %.Rmd
	$(R) 'qlearn::chapter_progress_image("$<")'
