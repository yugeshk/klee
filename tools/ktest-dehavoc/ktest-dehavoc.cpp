/* -*- mode: c++; c-basic-offset: 2; -*- */

//===-- ktest-dehavoc.cpp ---------------------------------------*- C++ -*-===//
//
//                     The KLEE Symbolic Virtual Machine
//
// This file is distributed under the University of Illinois Open Source
// License. See LICENSE.TXT for details.
//
//===----------------------------------------------------------------------===//

#include "klee/Internal/ADT/KTest.h"
#include "llvm/Support/CommandLine.h"
#include <map>
#include <vector>

namespace {
llvm::cl::opt<std::string> InputFile(llvm::cl::desc("<input ktest>"),
                                     llvm::cl::Positional, llvm::cl::init("-"));

llvm::cl::opt<std::string> OutputFile(llvm::cl::desc("<output ktest>"),
                                      llvm::cl::Positional,
                                      llvm::cl::init("-"));
}

int main(int argc, char **argv, char **envp) {
  llvm::cl::ParseCommandLineOptions(argc, argv);

  KTest *in = kTest_fromFile(InputFile.c_str());
  assert(in && "Error opening input KTEST file.");

  KTest out;
  out.numArgs = in->numArgs;
  out.args = in->args;
  out.symArgvs = in->symArgvs;
  out.symArgvLen = in->symArgvLen;

  std::vector<KTestObject> objects(in->objects, in->objects + in->numObjects);
  std::map<std::string, KTestObject> unique_objects;

  for (auto it : objects) {
    unique_objects[it.name] = it;
  }

  for (auto it = objects.begin(); it != objects.end();) {
    if (unique_objects.count(it->name)) {
      *it = unique_objects[it->name];
      unique_objects.erase(it->name);
      it++;
    } else {
      it = objects.erase(it);
    }
  }

  out.numObjects = objects.size();
  out.objects = objects.data();

  assert(kTest_toFile(&out, OutputFile.c_str()) &&
         "Error writing output KTEST file.");
}
