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
	$(R) 'library(qbit); if (yaml::read_yaml("index.yml")[["technologies"]] != "Theory") deploy("qbit-$(SLUG)", files = list.files("qbit-$(SLUG)", full.names = TRUE))'

deploy: $(OUT_JSON) $(OUT_ASSETS) index deploy-qbit
	$(R) 'library(qbit); deploy_course("$(SLUG)")'

deploy-no-qbit: $(OUT_JSON) $(OUT_ASSETS) index
	$(R) 'library(qbit); deploy_course("$(SLUG)")'

index: $(OUT_JSON)
	python3 script_create_index.py $(SLUG)

%.json : %.Rmd
	$(R) 'library(qlearn); rmarkdown::render("$<", output_format = "qlearn::qlearn")'

%.png : %.Rmd
	$(R) 'qlearn::chapter_progress_image("$<")'
