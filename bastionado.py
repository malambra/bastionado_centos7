#!/bin/python

import xml.etree.ElementTree as ET
import os, sys
import functions

#LIMITS
critical_limit=1
high_limit=3

#COUNTS
critical_count=0
high_count=0
medium_count=0
low_count=0
ok_count=0

score=0
evaluated=0

def calculate():
    global critical_limit, high_limit
    global critical_count, high_count, medium_count, low_count
    global ok_count
    global score, evaluated

    print ""
    print "-----------------------"
    print "Evaluated: %d points." % evaluated
    print "-----------------------"
    print "OK POINTS: %d" % ok_count
    print "CRITICAL POINTS: %d" % critical_count
    print "HIGH POINTS: %d" % high_count
    print "MEDIUM POINTS: %d" % medium_count
    print "LOW POINTS: %d" % low_count
    print "-----------------------"
    print "TOTAL SCORE: %d" % score
    print ""

    if critical_count > critical_limit:
        print "Criticals exceded."
        print "Dont PASS."
        sys.exit(1)
    elif high_count > high_limit:
        print "High exceded."
        print "Dont PASS."
        sys.exit(1)
    else:
        calc=score / evaluated
        if int(calc) < 4:
            print "PASS"
            print "Calculate Ratio: %d" % calc
            print "Need Ratio < 4"
            sys.exit(0)
        else:
            print "Dont PASS"
            print "Calculate Ratio: %d" % calc
            print "Need Ratio < 4"
            sys.exit(1)

def ponderar(result,lv,sc):
    global evaluated, ok_count, score, low_count, medium_count, high_count, critical_count
    evaluated=int(evaluated)+1

    if int(result) == 0:
        ok_count=int(ok_count)+1
    else:
        if lv == "LOW":
            low_count=int(low_count)+1
            score=int(score)+int(sc)
        elif lv == "MEDIUM":
            medium_count=int(medium_count)+1
            score = int(score) + int(sc)
        elif lv == "HIGH":
            high_count=int(high_count)+1
            score = int(score) + int(sc)
        elif lv == "CRITICAL":
            critical_count=int(critical_count)+1
            score = int(score) + int(sc)
        else:
            print "XML error, incorrect level."
            sys.exit(1)



def bastiona():
    tree = ET.parse('data.xml')
    root = tree.getroot()
    for item in root.findall('ITEM'):
        v_number = item.get('number')
        v_point = item.find('POINT').text
        v_title = item.find('TITLE').text
        v_description = item.find('DESCRIPTION').text
        v_caution = item.find('CAUTION').text
        v_audit = "functions."+item.find('AUDIT').text
        v_solution = "functions."+item.find('SOLUTION').text
        v_action = item.find('ACTION').text
        v_level = item.find('LEVEL').text
        v_score = item.find('SCORE').text

        #print number,point,title,description,caution,audit,solution,level
        #aux2=eval(solution)

        print "---------------------------------------"
        aux = eval(v_audit)
        print "Evaluating...."
        print "Point: "+v_point
        print "Title: "+v_title
        print "Description: "+v_description
        if aux == 0:
            print "Status: ...... OK"
            ponderar(aux, v_level, v_score)
        elif aux == 1:
            print "Status: ...... CRITICAL"
            print "Caution: "+v_caution
            if v_solution != "functions.dummy()":
                print "Solution: " + v_solution
                print "ACTIONS: " + v_action
                option = raw_input('Want solve it..[yes|NO]: ')
                if option == "yes":
                    aux = eval(v_solution)
                    if aux == 0:
                        ponderar(aux, v_level, v_score)
                        print "Status: ...... SOLVED."
                    elif aux == 1:
                        ponderar(aux, v_level, v_score)
                        print "Error on solving."
                else:
                    print "Dont try solve it."
                    ponderar(aux, v_level, v_score)
            else:
                ponderar(aux, v_level, v_score)



if __name__ == "__main__":
    bastiona()
    calculate()
