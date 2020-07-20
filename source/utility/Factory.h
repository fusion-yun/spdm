//
// Created by salmon on 17-4-12.
//

#ifndef SIMPLA_FACTORY_H
#define SIMPLA_FACTORY_H

#include "Logger.h"
#include "Singleton.h"
#include "TypeTraits.h"
#include <functional>
#include <iomanip>
#include <iostream>
#include <map>
#include <string>
namespace sp
{
template <typename TObj, typename... Args>
class Factory
{
public:
    Factory() = default;
    virtual ~Factory() = default;

    struct ObjectFactory
    {
        std::map<std::string, std::function<TObj*(Args const&...)>> m_factory_;
    };
    static bool has_creator(std::string const& k)
    {
        auto const& f = Singleton<ObjectFactory>::instance().m_factory_;
        return f.find(k) != f.end();
    }
    static std::string show_description(std::string const& k = "")
    {
        auto const& f = Singleton<ObjectFactory>::instance().m_factory_;
        std::string res;
        if (!k.empty())
        {
            auto it = f.find(k);
            if (it != f.end())
            {
                res = it->first;
            }
        }
        if (res.empty())
        {
            std::ostringstream os;
            os << std::endl
               << "Registered " << typeid(TObj).name() << " Creator:" << std::endl;
            for (auto const& item : f)
            {
                os << " " << item.first << std::endl;
            }
            res = os.str();
        }
        return res;
    };

    static int add(std::string const& k,
                   std::function<TObj*(Args const&...)> const& fun) noexcept
    {
        std::cout << k << std::endl;
        return Singleton<ObjectFactory>::instance().m_factory_.emplace(k, fun).second ? 1 : 0;
    };
    template <typename U>
    static int add(std::string const& k_hint,
                   std::enable_if_t<(std::is_constructible<U, Args...>::value)>* _p = nullptr) noexcept
    {
        return add(k_hint, [](Args const&... args) { return new U(args...); });
    };
    template <typename U>
    static int add(std::string const& k_hint,
                   std::enable_if_t<(!std::is_constructible<U, Args...>::value)>* _p = nullptr) noexcept
    {
        return add(k_hint.empty(), [](Args const&... args) { return U::create(args...); });
    };

private:
    template <typename... U>
    static TObj* _try_create(std::integral_constant<bool, true> _, U&&... args)
    {
        return new TObj(std::forward<U>(args)...);
    }
    template <typename... U>
    static TObj* _try_create(std::integral_constant<bool, false> _, U&&... args)
    {
        return nullptr;
    }

public:
    template <typename... U>
    static std::unique_ptr<TObj> create(std::string const& k, U&&... args)
    {
        if (k.empty())
        {
            return nullptr;
        }
        //        if (k.find("://") != std::string::npos) { return create_(ptr::DataTable(k), args...); }
        auto const& f = Singleton<ObjectFactory>::instance().m_factory_;
        TObj* res = nullptr;
        auto it = f.find(k);
        if (it != f.end())
        {
            res = it->second(std::forward<U>(args)...);
        }
        else
        {
            std::cout << show_description() << std::endl;

            RUNTIME_ERROR << "Can not find Creator \"" << k << "\"" << std::endl;
        }
        return std::unique_ptr<TObj>(res);
    }
};



} // namespace sp
#endif // SIMPLA_FACTORY_H
