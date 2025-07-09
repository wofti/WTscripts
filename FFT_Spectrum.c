/* (C) Wolfgang Tichy 2025

   Compute the coeffs co[k] for each frequency f_k = k/(N*dt) in a time
   series data set.
   r2c DFTs are always FFTW_FORWARD and c2r DFTs are always FFTW_BACKWARD.
   Thus:
   co[k]   = [ \sum_{j=0}^{N-1} data[j] exp(-i*2\pi*(j/N)*k) ] / N
   data[k] = \sum_{j=0}^{N-1} co[j] exp(i*2\pi*(j/N)*k)
*/
/*
gcc FFT_Spectrum.c -o FFT_Spectrum -lm -lfftw3
./FFT_Spectrum -d 0.0948 -n 10000 GRHD_rho0_pt0.t spec.f ; tgraph.py -m spec.f
*/

#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <limits.h>
#include <string.h>
//#include <complex.h>
#include <fftw3.h>

#define PI  3.14159265358979323846264338327950
#define PIh 1.57079632679489661923132169163975
#define PIq 0.785398163397448309615660845819876

#define STRLEN 262144
#define NDATAMAX 262144

/* funcs */
double Arg(double x, double y);


int main(int argc, char* argv[])
{
  char str[STRLEN];
  int i, col, first,nlines,last, linenum, ndata;
  double dt;
  double data[NDATAMAX];
  int infile_pos;
  FILE *in, *out;
  fftw_complex *co;
  fftw_plan p_r2c, p_c2r;

  if(argc < 2)
  {
    printf("Usage:\n"
           "%s [-d dt] [-c Col] [-o lineoffset] [-n nlines] "
           "<infile> <outfile>\n\n", argv[0]);
    printf("<infile>:   File with input time series\n");
    printf("<outfile>:  Output file with frequency spectrum\n");
    printf("dt:         Time step in infile\n");
    printf("Col:        Data-column we read (default is 2)\n");
    printf("lineoffset: Skip this many initial lines (default is 0)\n");
    printf("nlines:     Maximum number of lines to read (default is all)\n");
    printf("\n");
    printf("Examples:\n");
    printf("%s -c 2 -d 0.1 D.t spec.txt; tgraph.py spec.txt\n\n", argv[0]);
    exit(0);
  }

  /* default options */
  col = 2;
  dt  = 1.;
  first = 0;
  last = INT_MAX/2;
  nlines = -1; /* means arg not specified */

  /* parse command line options, which start with - */
  for(i=1; (i<argc)&&(argv[i][0] == '-'); i++)
  {
    char *astr = argv[i];

    if( (strcmp(astr+1,"d")==0) )
    {
      if(i>=argc-1) 
      {
        printf("no dt after -d\n");
        return -1;
      }
      dt = atof(argv[i+1]);
      i++;
    }
    else if( (strcmp(astr+1,"c")==0) )
    {
      if(i>=argc-1) 
      {
        printf("no col after -c\n");
        return -1;
      }
      col = atoi(argv[i+1]);
      i++;
    }
    else if( (strcmp(astr+1,"o")==0) )
    {
      if(i>=argc-1) 
      {
        printf("no line offset after -o\n");
        return -1;
      }
      first = atoi(argv[i+1]); /* first line (counting from 0) */
      i++;
    }
    else if( (strcmp(astr+1,"n")==0) )
    {
      if(i>=argc-1) 
      {
        printf("no number of line after -n\n");
        return -1;
      }
      nlines = atoi(argv[i+1]); /* number of lines */
      i++;
    }
    else
    {
      printf("unknown argument %s\n", astr);
      return -1;
    }
  }
  if(nlines > 0) last = first + nlines; /* last line */
  infile_pos = i;
  if(infile_pos > argc-2)
  {
    //printf("infile_pos=%d argc=%d\n", infile_pos, argc);
    printf("the two last args need to be filenames\n");
    return -1;
  }

  /* open file in */
  printf("# input file: %s",argv[infile_pos]);
  in=fopen(argv[i],"r");
  if(in==NULL)
  {
   printf(" not found.\n");
   return -2;
  }
  printf("\n");

  /* read infile */
  linenum = ndata = 0;
  while(fgets(str, STRLEN, in)!=NULL)
  {
    int c;
    char *tok;
    double dat;

    /* ignore comments */
    if(str[0]=='#') continue;

    /* ignore all outside first and last lines */
    if(linenum<first || linenum>=last) goto NextLine;

    /* go to column col in string str */
    c = 0;
    for(tok=strtok(str, " \t\n"); tok!=NULL; tok=strtok(NULL, " \t\n"))
    {
      //printf("tok=%s\n", tok);
      if(c==col-1)
      { 
        dat = atof(tok);
        break;
      }
      c++;
    }

    /* add dat to FFT array */
    data[ndata] = dat;
    ndata++;
    if(ndata>=NDATAMAX) { printf("NDATAMAX is too small!\n"); return -3; }

    /* inc linenum counter */
    NextLine:
    linenum++;
  }
  fclose(in);
  printf("# read %d lines from %s\n", ndata, argv[infile_pos]);
  //for(i=0; i<ndata; i++) printf("%.16g\n", data[i]);

  /* compute FFT of data */

  /* get mem for co */
  co = fftw_malloc(sizeof(fftw_complex) * ndata);
  //for(i=0; i<ndata; i++)
  //{
  //  co[i][0] = 42.0;
  //  co[i][1] = 43.0;
  //}

  /* make plans */
  p_r2c = fftw_plan_dft_r2c_1d(ndata, data, co, FFTW_ESTIMATE);
  p_c2r = fftw_plan_dft_c2r_1d(ndata, co, data, FFTW_ESTIMATE);

  /* do FFT of data */
  fftw_execute(p_r2c);

  for(i=0; i<ndata/2+1; i++)
  {
    co[i][0] /= ndata; /* accesses real part of co[i] */
    co[i][1] /= ndata; /* accesses imaginary part of co[i] */
    //co[i]/= ndata; /* do this if complex.h is included BEFORE fftw3.h */
  }

  fftw_destroy_plan(p_r2c);
  fftw_destroy_plan(p_c2r);


  /* open file out */
  printf("# output file: %s",argv[infile_pos+1]);
  out=fopen(argv[infile_pos+1],"wb");
  if(out==NULL)
  {
   printf(" could not be opened.\n");
   return -2;
  }
  printf("\n");

  fprintf(out, "#");
  for(i=0; i<argc; i++) fprintf(out, " %s", argv[i]);
  fprintf(out, "\n");
  fprintf(out, "# ---------------------------------------\n");
  fprintf(out, "# frequency  |co|  phase_co  Re_co  Im_co\n");

  for(i=0; i<ndata/2+1; i++)
  {
    double f_i = i / (ndata*dt);
    double re = co[i][0];
    double im = co[i][1];
    double amp = sqrt(re*re + im*im);
    double phase = Arg(re, im);
    fprintf(out, "%g  %g  %g  %g  %g\n", f_i, amp, phase, re, im);
  }
  fclose(out);

  fftw_free(co);
}


/* Arg function of z = x + iy : return value in (-PI,PI] */
double Arg(double x, double y)
{
  double arg;

  if(x==0.0)
  {
    if(y>0.0)  arg=PIh;
    else       arg=-PIh;
    if(y==0.0) arg=0.0;
  }
  else if(x<0)
  {
    if(y>=0.0)  arg=atan(y/x)+PI;
    else        arg=atan(y/x)-PI;
  }
  else
    arg=atan(y/x);

  return arg;
}
