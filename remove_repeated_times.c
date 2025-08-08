/* remove_repeated_times.c */
/* cleans up output of bam by removing lines with times that are
   less than or equal to the previous time */
/* (c) Wolfgang Tichy 2009 */


#define BUFLEN 134217728
#define STRLEN 262144

#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <ctype.h>
//#include "wolfio.c" 
#include <string.h>


/* flags denoting where we are in a block */
enum
{
  BLOCKSTART=1,
  BLOCKTIME=2,
  BLOCKEND=4
};


/* functions */

/* read everything (starting at position p) in str before the next
   space, \t or \n, write it into word,
   return the position of the space, \t or \n, 
   return EOF if end of string reached and no word found		*/
int sscan_word_at_p(const char *str, int p, char *word)
{
 int i;
 int strl=strlen(str);
 const char *pstr;
 
 if(p>=strl) return EOF;
 if(p<0)     return EOF;
 
 for(i=0;i+p<strl;i++)
   if(str[p+i]!=' ' && str[p+i]!='\t' && str[p+i]!='\n') break;

 if(p+i>=strl) return EOF;
 pstr=str+p+i;
 
 word[0]=0;
 sscanf(pstr,"%s",word);
 return strlen(word)+p+i;
}


/* global vars */

/* main prog. */
int main(int argc, char *argv[])
{
  int tcol;
  FILE *in;
  FILE *out;
  char *buffer;
  char str[STRLEN];
  char str2[STRLEN];
  char str3[STRLEN];
  char blockstart[STRLEN];
  char tstr[STRLEN];
  int loc, writeblock, i, col, p, tcolarg;
  char *astr;
  double time, blocktime, timeshift;
  
  buffer = (char *) calloc(BUFLEN, sizeof(char));

  printf("# remove_repeated_times \n");
  if(argc<3 || argc>11)  
  {
   printf("# usage: remove_repeated_times [-B blk] [-T tstr] [-C tcol] in.dat out.dat\n");
   printf("# options: -B blk   use label blk to search for start of new block (default \"\")\n");
   printf("#          -T tstr  use label tstr to search for time entries (default \"\")\n");
   printf("#          -C tcol  read time in column tcol (default 1)\n");
   printf("#          -S dt    shift time by dt\n");
   printf("# examples:\n");
   printf("# remove_repeated_times -B \"# iteration\" -T time -C 4 in.dat out.dat\n");
   printf("# remove_repeated_times in.dat l ; awk '{if($1!=\"\\\"\") print $0}' l > out.dat\n");
   printf("# remove_repeated_times -C 7 -S 6.1 moving_puncture_integrate1.txyz10.orig l\n");
   return -1;
  }

  /* default options */
  tcolarg=0;
  tcol=1;
  tstr[0]=0;
  blockstart[0]=0;
  timeshift=0.0;

  /* parse command line options, which start with - */
  for(i=1; (i<argc)&&(argv[i][0] == '-'); i++)
  {
   astr = argv[i];

   if( (strcmp(astr+1,"C")==0) )
   {
     if(i>=argc-1) 
     {
       printf("no tcol after -C\n");
       return -1;
     }
     tcolarg=1;
     tcol=atoi(argv[i+1]);
     i++;
   }
   else if( (strcmp(astr+1,"T")==0) )
   {
     if(i>=argc-1) 
     {
       printf("argument tstr is needed after -T\n");
       return -1;
     }
     sprintf(tstr, "%s", argv[i+1]);
     i++;
   }
   else if( (strcmp(astr+1,"B")==0) )
   {
     if(i>=argc-1) 
     {
       printf("argument blk is needed after -B\n");
       return -1;
     }
     sprintf(blockstart, "%s", argv[i+1]);
     i++;
   }
   else if( (strcmp(astr+1,"S")==0) )
   {
     if(i>=argc-1) 
     {
       printf("no timeshift after -S\n");
       return -1;
     }
     timeshift=atof(argv[i+1]);
     i++;
   }
   else 
   {
     printf("remove_repeated_times: unknown argument %s\n", astr);
     return -1;
   }
  }

  //printf("i=%d argc=%d\n", i, argc);

  /* info about colmuns */
  printf("# time is read from column %d", tcol);
  if(tstr[0]!=0)
    printf(" of lines that contain %s\n", tstr);
  else
    printf("\n");

  /* sanity checks */
  if(tstr[0]!=0)
  {
    if(blockstart[0]==0)
    {
      printf("could not find -B argument\n");
      return -10;
    }
    if(tcolarg==0)
    {
      printf("could not find -C argument\n");
      return -10;
    }
  }
  if(blockstart[0]!=0)
  {
    if(tstr[0]==0)
    {
      printf("could not find -T argument\n");
      return -10;
    }
  }
  
  /* open file in */
  printf("# input file: %s",argv[i]);
  in=fopen(argv[i],"r");
  if(in==NULL)
  {
   printf(" not found.\n");
   return -2;
  }
  printf("\n");

  /* open file out */
  printf("# output file: %s",argv[i+1]);
  out=fopen(argv[i+1],"wb");
  if(out==NULL)
  {
   printf(" could not be opened.\n");
   return -2;
  }
  printf("\n");

  /* set initial time and go through file in */
  time=-1e300;
  writeblock=1;
  while(fgets(str, STRLEN, in)!=NULL)
  {
    /* set flag loc */
    loc=0;
    if(strstr(str, blockstart)!=NULL) loc = loc | BLOCKSTART;
    if(strstr(str, tstr)!=NULL)       loc = loc | BLOCKTIME;

    /* write previous buffer if we are at end of a block, i.e. if there is a
       new BLOCKSTART */
    if(loc & BLOCKSTART)
    {
      if(writeblock) fprintf(out, "%s", buffer);
      buffer[0]=0;
      writeblock=1;
    }

    /* get time of block and decide if we write it */
    if(loc & BLOCKTIME)
    {
      for(p=0, col=1; col<=tcol; col++)  p=sscan_word_at_p(str, p, str2);
      if(p==EOF)  str2[0]=0;
      blocktime=atof(str2);
      if(isdigit(str2[0]) || str2[0]=='-' || str2[0]=='+')
      {
        if(blocktime<=time)  writeblock=0;
        else                 time=blocktime;

        /* shift time */
        if(timeshift!=0.0)
        {
          i=p-strlen(str2);  /* i = pos of begin of str2 in str */
          strcpy(str3, str);
          str3[i]=0;         /* end str3 exactly before time number in str */
          sprintf(str2, "%.16g", blocktime+timeshift); /* change time string */
          strcat(str3, str2);  /* append new time */
          strcat(str3, str+p); /* append rest of str */
          strcpy(str, str3);   /* copy str3 into str */
        }
      }
      else
      {
        if(tstr[0]!=0)
        {
          printf("time at column %d is %s. That is not a number!\n", tcol, str2);
          return -10;
        }
      }
    }
/*
    printf("%s", str);
    printf("|blockstart=%s| |tstr=%s| loc=%d time=%f\n",
    blockstart, tstr, loc, time);
*/
    /* add newest string to buffer */
    sprintf(buffer+strlen(buffer), "%s", str);
  }
  /* write last buffer */
  if(writeblock) fprintf(out, "%s", buffer);
  buffer[0]=0;

  /* close files, free memory and return */
  fclose(in);
  fclose(out);
  free(buffer);

  return 0; 
}
