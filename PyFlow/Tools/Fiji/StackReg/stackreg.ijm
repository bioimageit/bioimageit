macro stackreg{

	// parse args
	args = parseArgs();

	// open the data
	open(args[0]);
	image = getTitle();

	operator = args[1];
	operator=replace(operator,"_"," ");

	// run
	run("StackReg ", "transformation=["+operator+"]");

	// save result image
	saveAs("TIFF", args[2]);

}

function parseArgs(){
	argsStr = getArgument()
	argsStr = substring(argsStr, 1, lengthOf(argsStr)); // remove first char
	argsStr = substring(argsStr, 0, lengthOf(argsStr)-1); // remove last char
	print(argsStr);
	args = split(argsStr, ",");
	for (i=0 ; i < args.length ; i++){
		print(args[i]);
	}
	return args;
}
