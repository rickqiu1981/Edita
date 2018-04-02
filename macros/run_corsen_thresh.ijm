//Calculate minimal and maximal grey values in a stack serie
function getstackMinandMax(){
    stackMinandMax=newArray(65535,0,0,0);
    for(i=0;i<nSlices;i++){
        setSlice(i+1);
        getRawStatistics(npix,mean,min,max,std,hist);
        if (min<stackMinandMax[0]) {
            stackMinandMax[0]=min;
            stackMinandMax[2]=i+1;
        }
        if (max>stackMinandMax[1]) {
            stackMinandMax[1]=max;
            stackMinandMax[3]=i+1;
        }
    }
    return stackMinandMax;
}


//Apply by subtraction the mask to the image to be treated 
function applyMask(mask,im){
    selectImage(mask);
    run("Duplicate...", "title=inter-mask");
    inter=getImageID();
    run("16-bit");
    run("Invert");
    run("Multiply...", "value=16");
    selectImage(im);
    if(nSlices!=1){ 
        m=getstackMinandMax();
        setSlice(m[3]);
    }
    run("Duplicate...", "title=slicecalculator");
    slicecalc=getImageID(); 
    imageCalculator("Subtract create",slicecalc,inter); 
    rename("result");
    run("32-bit");
    setThreshold(1,4095);
    run("NaN Background");
    slicecalcres=getImageID();
    return slicecalcres;
}

//Calculate cumulate sum of an array  
function getnPix(hist){
    npix=0;
    for(i=0;i<hist.length;i++){
        npix=npix+hist[i];
    }
    return npix;
}


//calculate median value of an array (count: cumulate sum of the array)
function getMedian(hist, count) {
    n = hist.length;
    sum = 0;
    i = -1;
    count2 = count/2;
    do {
        sum += hist[++i];
    } while (sum<=count2 && i<4095);
    return i;
}


//Calculate the window of intensities used for the image treatment
//(based on histogramm analysis and choosen coefficent)
function getWindowanalyse(slicecalc,coeff){
    selectImage(slicecalc);
    getRawStatistics(n,meanc,minc,maxc,stdc);
    getHistogram(values,histc,4096,0,4096);
    npixc=getnPix(histc);	
    medianc=getMedian(histc, npixc);
    newmin1=medianc+(coeff-2)*stdc; if(newmin1<minc) newmin1=minc;
    newmax1=1.5*maxc; if(newmax1>4095) newmax1=4095;
    newmin2=medianc+coeff*stdc; if(newmin2<minc) newmin2=minc;	
    newmax2=1.2*maxc; if(newmax2>4095) newmax2=4095;
    selectImage(slicecalc); close();
    windowa=newArray(newmin1,newmax1,newmin2,newmax2);
    return windowa;
}


//Apply image processing
function applyTraitement(im,windowa,coeff,med,conti){
    selectImage(im);
    run("Duplicate...", "title=inter-1 duplicate");
    im1=getImageID();
    run("Duplicate...", "title=inter-2 duplicate");
    im2=getImageID();

    selectImage(im1);
    setSlice(1);
    setMinAndMax(windowa[0],windowa[1]);
    run("8-bit");
    run("Convolve...", "text1=[-1 -1 -1 -1 -1 -1 -1 -1 -1 -1 -1 -1 24 -1 -1 -1 -1 -1 -1 -1 -1 -1 -1 -1 -1 ] normalize stack");
    if(conti!=0) {setMinAndMax(0,128);}
    if(med!=0){run("Median...", "radius="+med+" stack");}
    selectImage(im2);
    setMinAndMax(windowa[2],windowa[3]);
    run("8-bit");

    imageCalculator("Add create stack", im1,im2);
    selectImage(im1); close();
    selectImage(im2);close();
    rename("traitement_coefficient"+coeff+"_median"+med+"_continuit�"+conti);
}

function image_processing(mask,im,coeff,med,conti) {
    slicecal=applyMask(mask,im);
    windowa=getWindowanalyse(slicecal,coeff);
    applyTraitement(im,windowa,coeff,med,conti);
    run("Tile");
    result = getImageID();
    return result;
}

function process_stack(input_template, output_filename, coeff, med, conti, max, thresh1, thresh2) {
    for (i=1; i<6; i++) {
        open(replace(input_template,"?",i));
    }
    run("Images to Stack");
    setMinAndMax(0,max);

    orig=getImageID();
    run("Duplicate...", "title=orig_8bit");
    run("8-bit");
    run("16-bit");
    orig_8bit_values=getImageID();
    run("Duplicate...", "duplicate range=1-5");
    setAutoThreshold(thresh1+" dark");
    setOption("BlackBackground", true);
    run("Convert to Mask", "method=Mean background=Dark black");
    mask=getImageID();
    // image processing goes here ....
    ip_result=image_processing(mask,orig_8bit_values,coeff,med,conti);
    selectImage(ip_result);

    setAutoThreshold(thresh2+" dark");
    setOption("BlackBackground", true);
    run("Convert to Mask", "method=MaxEntropy background=Dark black");
    run("Median...", "radius=1 stack");
    mask2=getImageID();
    masked=applyMask(mask2,orig_8bit_values);
    selectImage(masked);
    run("8-bit"); // 32-bit with NaNs confuses everybody

    // save result
    save(output_filename);
}

function interpret_args_and_process(args_str) {
    args = split(args_str,',');

    // expect arguments:
    // template, out_filename, coeff (float), median (int), conti (0 or 1), max (int)
    // thresh1, thresh2 (ImageJ threshold type)
    if (args.length != 8) {
        exit("The run_corsen macro expects 8 arguments");
    }

    template = args[0];
    output = args[1];
    coeff = parseFloat(args[2]);
    median = parseInt(args[3]);
    conti = parseInt(args[4]);
    max = parseInt(args[5]);
    thresh1 = args[6];
    thresh2 = args[7]);

    if (!File.exists(replace(template,'?','1'))) { exit("Template file not found: "+template); }
    if (!File.exists(File.getParent(output))) { exit("Directory does not exist for output: "+output); }
    if (isNaN(coeff)) { exit("coeff (3rd parameter) must be a floating-point number"); }
    if (isNaN(median)) { exit("median (4th parameter) must be an integer"); }
    if (conti != 0 && conti != 1) { exit("conti (5th parameter) must be 0 or 1"); }
    if (isNaN(max)) { exit("max (6th parameter) must be an integer"); }

    process_stack(template, output, coeff, median, conti, max, thresh1, thresh2);

    run("Close All");
}

function main() {
    args_file = getArgument();

    if (!File.exists(args_file)) { exit("Arguments file for corsen macro not found: "+args_file); }

    args_str = File.openAsString(args_file);
    lines = split(args_str,"\n");
    for (i=0; i<lines.length; i++) {
        if (lengthOf(lines[i]) != 0) { // skip blank lines
            interpret_args_and_process(lines[i]);
        }
    }
}

main();
run("Quit");
