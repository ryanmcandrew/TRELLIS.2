// MSVC does not export inherited constructors for DLL-marked derived classes.
// c10::ValueError(SourceLocation, string) is missing from c10.dll because
// `using Error::Error;` doesn't generate a separate exported thunk.
// Alias it to c10::Error(SourceLocation, string) which IS exported and is
// identical at the machine level (ValueError adds no data members).
#ifdef _MSC_VER
#pragma comment(linker, \
    "/ALTERNATENAME:__imp_??0ValueError@c10@@QEAA@USourceLocation@1@" \
    "V?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@@Z=" \
    "__imp_??0Error@c10@@QEAA@USourceLocation@1@" \
    "V?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@@Z")
#endif
