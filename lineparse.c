// $Id$
// $Revision$
// $Date$


#include<stdio.h>
#include<stdlib.h>

#ifdef PYTHON_EXTENSION
#include<Python.h>
volatile sig_atomic_t kb_interrupt = 0; //flag set check keyboard interrupt occurs
#endif

// **************
//
// Code for using code as a python module
//
// **************

#ifdef PYTHON_EXTENSION

//handler for SIGINT
void kb_interrupt_handler(int sig) {
    kb_interrupt = 1;  //set global flag, cause process to exit.
}

static PyObject *makePythonOutput() {
    //copies the contents of the rateBuffer into a Python Tuple to be returned by the module    
    //PyObject *returnTup;    //tuple to be returned
    //PyObject *itemTup;      //tuple for one pair (error, rates)
    //PyObject *rateTup;      //tuple for a set of rates
    //int c; int d;
    //returnTup = PyTuple_New(RATE_BUFFER_SIZE);
    //for(c=0; c < 10; c++){
    //    rateTup = PyTuple_New(frame->annualRecords);
    //    for(d=0; d < frame->annualRecords; d++){
    //        PyTuple_SetItem(rateTup,d, PyFloat_FromDouble(frame->solutionBuffer[c]->rates->item[d]));
    //    }
    //    itemTup = PyTuple_New(2);
    //    PyTuple_SetItem(itemTup,0,PyFloat_FromDouble(frame->solutionBuffer[c]->error));
    //    PyTuple_SetItem(itemTup,1,rateTup);
    //    PyTuple_SetItem(returnTup,c,itemTup);
    //}
    //return returnTup;
    return NULL;
}


static PyObject *split(PyObject *self, PyObject *args) {
    //Format of parsed data:
    //yearsOfData, recordsPerYear, companyCount, naiveRates, tuple of company data
    //each tuple of company data is (ticker,target,tuple annual data)
    //each tuple of annual data is (records)
    PyObject *output = NULL;
    sig_t previousHandler;
    previousHandler = signal(SIGINT, kb_interrupt_handler); //set signal handler
    

    signal(SIGINT, previousHandler); //turn off new kb-interrupt handler
    
    //PyErr_SetObject(PyExc_KeyboardInterrupt, NULL); //tell python a kb-break occurred
    makePythonOutput();
    return output;
}

static PyObject *test(PyObject *self, PyObject *args) {
    //const char *command;
    char *str;
    int len;
    int c;
    PyObject *origStr;
    PyObject *utfStr;
    PyObject *secondTup;
    if (!PyArg_ParseTuple(args, "O", &origStr))
        return NULL;
    utfStr = PyObject_CallMethod(origStr,"encode","s","utf-32"); //utf-32 encode string
    secondTup = PyTuple_New(1);
    PyTuple_SetItem(secondTup,0,utfStr);
    PyArg_ParseTuple(secondTup, "s#", &str, &len);
    
    for(c = 0; c < len; c++){
        if (str[c] == 0) {printf("\\0");}
        else{printf("%c",str[c]);}
    }
    return Py_None;
}

static PyObject *version(PyObject *self, PyObject *args) {
    //const char *command;
    return Py_BuildValue("s", "$Id$");
}

static PyMethodDef lineParseMethods[] = {
    //need one function for taking a job and returning the results.
    {"split", split, METH_VARARGS, "Takes a UTF-32 unicode string.  Returns a list of strings, representing the splitting of the string by commas that are not included in quotes."},
    {"version", version, METH_VARARGS, "Returns version string for module."},
    {"test", test, METH_VARARGS, "Multiply a number by four."},
    {NULL,NULL,0,NULL}
};

PyMODINIT_FUNC initlineparse(void) { //initialize list of methods for interpreter
    (void) Py_InitModule("lineparse",lineParseMethods);
}
#endif
