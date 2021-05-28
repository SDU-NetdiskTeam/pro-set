all: seafes.tar.gz
dist: all

poi/ExtractText.class : ExtractText.java
	javac -cp poi/commons-codec-1.5.jar:poi/poi-excelant-3.9-20121203.jar:poi/commons-logging-1.1.jar:poi/poi-ooxml-3.9-20121203.jar:poi/dom4j-1.6.1.jar:poi/poi-ooxml-schemas-3.9-20121203.jar:poi/junit-3.8.1.jar:poi/poi-scratchpad-3.9-20121203.jar:poi/log4j-1.2.13.jar:poi/stax-api-1.0.1.jar:poi/poi-3.9-20121203.jar:poi/xmlbeans-2.3.0.jar:poi/poi-examples-3.9-20121203.jar -d poi ExtractText.java

poi/ExtractText.jar: poi/ExtractText.class
	cd poi && jar cvfm ExtractText.jar manifest.mf ExtractText.class

seafes.tar.gz: poi/ExtractText.jar
	cd .. && \
	tar czv \
	--exclude='*.git*' \
	--exclude='*.log' \
	--exclude='*~' \
	--exclude='*#' \
	--exclude='*.gz' \
	--exclude='*.pyc' \
	--exclude='*.class' \
	--exclude='*.java' \
	--exclude='*.mf' \
	--exclude='tests/*' \
	--exclude='.cache/*' \
	--exclude='local_settings.py' \
	--exclude='README.md' \
	--exclude='tests*' \
	--exclude='words.txt' \
	--exclude='Makefile' \
	--exclude='*.lock' \
	--exclude='pytest.ini' \
	--exclude='run.sh*' \
	-f seafes.tar.gz seafes/ && \
	mv seafes.tar.gz seafes/

clean:
	rm -f poi/ExtractText.class poi/ExtractText.jar seafes.tar.gz
