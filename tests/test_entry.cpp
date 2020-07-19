#include "Entry.h"
#include <iostream>

#define CATCH_CONFIG_MAIN
#include "catch.hpp"

TEST_CASE("SpDocument Create", "[SpDB]")
{
    sp::Entry entry;

    entry.set_attribute("A", std::string("a"));
    entry.set_attribute("B", std::string("b"));
    entry["A"].set_value<std::string>("1234");
    entry["B"].set_value<std::string>("5678");
    

    for (auto const& v : entry.children())
    {
        std::cout << " " << v.get_value<std::string>() ;
    }
    std::cout << std::endl;
    // std::cout << "====================================" << std::endl;
    // entry.as_table()["C"].as_array().push_back().as_scalar().set_value<std::string>("1234");

    // // entry.set_value<std::string>("1234");
    // std::cout << entry << std::endl;

    // // std::cout << "====================================" << std::endl;

    // // entry.append().set_value<std::string>("4567");
    // std::cout << "====================================" << std::endl;

    // entry.as_array().push_back().as_scalar().set_value<std::string>("7890");

    // std::cout << entry << std::endl;

    // REQUIRE(entry.child("C").child(0).get_value<std::string>() == "1234");
}