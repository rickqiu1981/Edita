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
//    run("Duplicate...", "title=inter-mask");
    inter=getImageID();
    run("16-bit");
    run("Invert");
    run("Multiply...", "value=16");
    selectImage(im);
    if(nSlices!=1){ 
        m=getstackMinandMax();
        if (m[3] == 0) m[3] = 1;//by Ricky, because the stack starts from 1
             
        setSlice(m[3]);//apply background subtraction to the slice with the largest intensity pixel
    }
    run("Duplicate...", "title=slicecalculator");
    slicecalc=getImageID();
    imageCalculator("Subtract create",slicecalc,inter); 
    rename("result");
    run("32-bit");
    setThreshold(1,4095);
    run("NaN Background");
    slicecalcres=getImageID();
//    save("test.tif");
    return slicecalcres;
}
function applyMask_zq(mask,im){
//apply masks of z-stack onto each planes, by Ricky 12/05/2014
    run("Misc...", "divide=Infinity hide run");//by Ricky 07/05/2014, set the stack process as the default option
    selectImage(mask);
    run("Duplicate...","duplicate range=1-5");
    inter=getImageID();
    run("16-bit","stack");
    run("Invert","stack");
    run("Multiply...", "value=16");
//    rename("mask");
    selectImage(im);
    run("Duplicate...", "duplicate range=1-5");
  //  rename("raw");
    slicecalc=getImageID();
//    imageCalculator("Subtract create",slicecalc,inter); 
    imageCalculator("subtract create stack",slicecalc,inter);//by ricky ,stack processing,12/05/2014 
    rename("result");
    run("32-bit","stack");
    setThreshold(1,4095);
    run("NaN Background","stack");
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
    newmin1=medianc+(coeff-2)*stdc; if(newmin1<minc) newmin1=minc;//so the effective c is -1, by Ricky
    newmax1=1.5*maxc; if(newmax1>4095) newmax1=4095;//why?another mystery,, by Ricky
    newmin2=medianc+coeff*stdc; if(newmin2<minc) newmin2=minc;	
    newmax2=1.2*maxc; if(newmax2>4095) newmax2=4095;//why?another mystery, by Ricky
    windowa=newArray(newmin1,newmax1,newmin2,newmax2);
    return windowa;
}


//Apply image processing
function applyTraitement(im,windowa,coeff,med,conti){
    selectImage(im);
    run("Duplicate...", "title=inter-10 duplicate");
    im1=getImageID();
    run("Duplicate...", "title=inter-20 duplicate");
    im2=getImageID();

    selectImage(im1);
    setSlice(1);
    setMinAndMax(windowa[0],windowa[1]);//clip the intensities without the range , by ricky 
    run("8-bit","stack");
    run("Convolve...", "text1=[-1 -1 -1 -1 -1 -1 -1 -1 -1 -1 -1 -1 24 -1 -1 -1 -1 -1 -1 -1 -1 -1 -1 -1 -1 ] normalize stack");//do laplacian filter, by ricky 
    if(conti!=0) {setMinAndMax(0,128);}
    if(med!=0){run("Median...", "radius="+med+" stack");}//the median fifltering the laplacian filtered result, by ricky 
    selectImage(im2);
    setMinAndMax(windowa[2],windowa[3]);//clip the intensities without the range on the raw data again, by ricky 
    run("8-bit","stack");
    run("Misc...", "divide=Infinity hide run");//by Ricky 07/05/2014, set the stack process as the default option
    imageCalculator("Add create stack", im1,im2);//needed to add a default option to work on all slices
    imresult = getImageID();//by ricky 30/04/2014
    selectImage(im1);
    selectImage(im2);
    selectImage(imresult)
;//by ricky 30/04/2014
    rename("traitement_coefficient"+coeff+"_median"+med+"_continuit"+conti);
    return getImageID();
}

function image_processing(mask,im,coeff,med,conti) {
    slicecal=applyMask(mask,im);// this is used to get the coefficient from the slice with largest intensity pixel 
    windowa=getWindowanalyse(slicecal,coeff);// the coefficient 
    return applyTraitement(im,windowa,coeff,med,conti);
}

function identify_objects(im_id) {
    selectImage(im_id);
    setThreshold(1,255);
    run("Set Measurements...", "area mean standard min center shape skewness kurtosis redirect=None decimal=3");
    run("Analyze Particles...", "size=0-Infinity circularity=0.00-1.00 show=Nothing display clear");
    if (nResults == 0) {
        return;
    }
    // in batch mode results go straight to stdout ....
}
function identify_objects_3D(im_id){
// by Ricky 13/05/2014
    selectImage(im_id);
    setThreshold(1,255);
//    run("3D Viewer");
    run(" 3D OC Options", "volume mean_gray_value std_dev_gray_value minimum_gray_value maximum_gray_value centre_of_mass redirect=None decimal=3");
    run(" 3D objects counter", "threshold=5 slice=5 min.=1 max.=13223123 statistics"); 
    if (nResults == 0) {
        return;
    }
}

function process_stack(image_in, image_out, prepend_cols,coeff, med, conti, min, max, mask1, mask2) {
    run("Misc...", "divide=Infinity hide run");//by Ricky 07/05/2014, set the stack process as the default option

    open(image_in);
    setMinAndMax(min,max);

    orig=getImageID();

//    run("Duplicate...", "title=orig_8bit");// this is where the bug is 
    run("Duplicate...", "duplicate range=1-5");//revised by Ricky
    run("8-bit","stack");
    run("16-bit","stack");
    orig_8bit_values=getImageID();
    run("Duplicate...", "duplicate range=1-5");

     
    setAutoThreshold(mask1+" dark");
    setOption("BlackBackground", true); // needed for thresholding
    run("Convert to Mask", "method="+mask1+" background=Dark black");
    mask=getImageID(); // Mask 1
   // image processing goes here ....
    ip_result=image_processing(mask,orig_8bit_values,coeff,med,conti);
     selectImage(ip_result);
    setAutoThreshold(mask2+" dark");
    setOption("BlackBackground", true); // needed for thresholding
    run("Convert to Mask", "method="+mask2+" background=Dark black");
//    save("before_watershed_stack.tif");// by Ricky
    run("Watershed","stack");
//    save("after_watershed_stack.tif");//by Ricky
    run("Median...", "radius=1 stack");
    mask2=getImageID(); // Mask 2
//    masked=applyMask(mask2,orig_8bit_values);//commented by Ricky
    masked = applyMask_zq(mask2,orig_8bit_values);//by Ricky 12/05/2014, apply masks of each plane onto the corresponding multi-plane raw images!
    
    selectImage(masked);
    run("8-bit","stack"); // 32-bit with NaNs confuses everybody

    // save result
    save(image_out);

    // tag for objects
  
    print("prepend:"+prepend_cols+"\t"+File.getName(image_in));
    // save objects
    run("Set Scale...", "distance=1 pixel=1 unit=pixel known=1");
    identify_objects_3D(getImageID());
    //print result by Ricky
    if (nResults >0){
    	print("\tvolume (pixel^3)\tmean\tstd\tmin\tmax\txm\tym\tzm\n");
    	for(i=0;i<nResults;i++)
		{a = getResultString("Volume (pixel^3)", i) + "\t"+getResultString("Mean", i)+ "\t"+getResultString("StdDev", i)+ "\t"+getResultString("Min", i) +  "\t"+getResultString("Max", i)+ "\t"+getResultString("XM", i)  + "\t"+getResultString("YM", i) + "\t"+getResultString("ZM", i);
		print(i+1+"\t"+a);}
    }
  //  saveAs("Results","/data/Results2.xls");
 //    print(nResults);

//    identify_objects_3D(getImageID());//group the object in 3D using the  connectted component by Ricky (unsure about the ), 13/05/2014
    run("Close All");
    

}



function interpret_args_and_process(args_str) {
    args = split(args_str,',');

    // expect arguments:
    // image_in, out_filename, coeff (float), median (int), conti (0 or 1), min (int), max (int), mask1 method, mask2 method
    if (args.length != 10) {
        exit("The run_corsen macro expects 10 arguments, got "+args.length+"\n"+args_str);
    }

    image_in = args[0];
    output = args[1];
    prepend_cols = args[2]; // tab-separated values to add to the start of each line
    coeff = parseFloat(args[3]);
    median = parseInt(args[4]);
    conti = parseInt(args[5]);
    min = parseInt(args[6]);
    max = parseInt(args[7]);
    mask1 = args[8];
    mask2 = args[9];

    if (!File.exists(image_in)) { exit("Template file not found: "+template); }
    if (!File.exists(File.getParent(output))) { exit("Directory does not exist for output: "+output); }
    if (isNaN(coeff)) { exit("coeff (4rd parameter) must be a floating-point number"); }
    if (isNaN(median)) { exit("median (5th parameter) must be an integer"); }
    if (conti != 0 && conti != 1) { exit("conti (6th parameter) must be 0 or 1"); }
    if (isNaN(min)) { exit("min (7th parameter) must be an integer"); }
    if (isNaN(max)) { exit("max (8th parameter) must be an integer"); }

    process_stack(image_in, output, prepend_cols, coeff, median, conti, min, max, mask1, mask2);
}

function main() {
    args_file = getArgument();
//    args_file = "/data/project/HBP/melissa/run_corsen_on_section_3ZltOg/corsen_in_QJpOBY.csv"
    if (!File.exists(args_file)) { exit("Arguments file for corsen macro not found: "+args_file); }
//     interpret_args_and_process(lines[0]);
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
