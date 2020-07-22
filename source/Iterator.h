#ifndef SP_ITERATOR_H_
#define SP_ITERATOR_H_

#include <functional>
#include <iterator>
#include <memory>
namespace sp
{

//##############################################################################################################
// iterator
template <typename... T>
class Iterator;

template <typename T>
struct IteratorTraits : public std::iterator<std::input_iterator_tag, T>
{
    typedef std::iterator<std::input_iterator_tag, T> base_type;
    using base_type::difference_type;
    using base_type::pointer;
    using base_type::reference;
    using base_type ::value_type;
};
template <typename T>
struct IteratorTraits<std::shared_ptr<T>>
{
    typedef ptrdiff_t difference_type;
    typedef std::shared_ptr<T> pointer;
    typedef T& reference;
    typedef T value_type;
};

template <typename T, typename... Others>
struct IteratorProxy;

template <typename T>
class IteratorProxy<T>
{
public:
    typedef IteratorProxy<T> this_type;
    typedef std::iterator_traits<T*> traits_type;
    typedef typename traits_type::pointer pointer;
    typedef typename traits_type::reference reference;
    typedef typename traits_type::value_type value_type;

    IteratorProxy() = default;

    IteratorProxy(const IteratorProxy& other) = default;

    IteratorProxy(IteratorProxy&& other) = default;

    virtual ~IteratorProxy() = default;

    virtual bool is_derived_from(const std::type_info& tinfo) const { return tinfo == typeid(this_type); }

    virtual this_type* copy() const = 0;

    virtual IteratorProxy<const T>* const_copy() const = 0;

    virtual pointer next() = 0;
};

template <typename T, typename IT>
class IteratorProxy<T, IT> : public IteratorProxy<T>
{
public:
    typedef IteratorProxy<T> base_type;
    typedef IteratorProxy<T, IT> this_type;

    using typename base_type::pointer;
    using typename base_type::reference;
    using typename base_type::value_type;

    typedef IT iterator;

    IteratorProxy(iterator&& it) : m_it_(std::move(it)) {}

    IteratorProxy(const iterator& it) : m_it_(it) {}

    IteratorProxy(const this_type& other) : base_type(other), m_it_(other.m_it_) {}

    IteratorProxy(this_type&& other) : base_type(other), m_it_(std::move(other.m_it_)) {}

    virtual ~IteratorProxy() = default;

    bool is_derived_from(const std::type_info& tinfo) const override { return tinfo == typeid(this_type) || base_type::is_derived_from(tinfo); }

    base_type* copy() const override { return new this_type(*this); };

    IteratorProxy<const T>* const_copy() const { return new IteratorProxy<const T, IT>(m_it_); }

    pointer next() override
    {
        pointer p = const_cast<pointer>(&(*m_it_));
        ++m_it_;
        return p;
    }

protected:
    iterator m_it_;
};

template <typename T>
class IteratorProxy<T, std::shared_ptr<std::remove_const_t<T>>> : public IteratorProxy<T>
{
public:
    typedef IteratorProxy<T> base_type;
    typedef IteratorProxy<T, std::shared_ptr<std::remove_const_t<T>>> this_type;

    using typename base_type::pointer;
    using typename base_type::reference;
    using typename base_type::value_type;

    typedef std::shared_ptr<std::remove_const_t<T>> iterator;

    IteratorProxy(iterator&& it) : m_it_(std::move(it)), m_pos_(0) {}

    IteratorProxy(const iterator& it) : m_it_(it), m_pos_(0) {}

    IteratorProxy(const this_type& other) : base_type(other), m_it_(other.m_it_), m_pos_(other.m_pos_) {}

    IteratorProxy(this_type&& other) : base_type(other), m_it_(std::move(other.m_it_)), m_pos_(other.m_pos_) {}

    virtual ~IteratorProxy() = default;

    bool is_derived_from(const std::type_info& tinfo) const override { return tinfo == typeid(this_type) || base_type::is_derived_from(tinfo); }

    base_type* copy() const override { return new this_type(*this); };

    IteratorProxy<const T>* const_copy() const { return new IteratorProxy<const T, iterator>(m_it_); }

    pointer next() override
    {
        ++m_pos_;
        return m_it_.get() + m_pos_ - 1;
    }

protected:
    iterator m_it_;
    size_t m_pos_;
};

template <typename T, typename IT, typename Mapper>
struct IteratorProxy<T, IT, Mapper> : public IteratorProxy<T>
{
public:
    typedef IteratorProxy<T, IT, Mapper> this_type;
    typedef IteratorProxy<T> base_type;
    typedef Mapper mapper_t;
    typedef IT iterator;

    using typename base_type::pointer;
    using typename base_type::value_type;

    IteratorProxy(iterator const& it, mapper_t const& mapper) : m_it_(it), m_mapper_(mapper) {}
    IteratorProxy(iterator&& it, mapper_t&& mapper) : m_it_(std::move(it)), m_mapper_(std::move(mapper)) {}
    IteratorProxy(this_type const& other) : m_it_(other.m_it_), m_mapper_(other.m_mapper_) {}
    IteratorProxy(this_type&& other) : m_it_(std::move(other.m_it_)), m_mapper_(std::move(other.m_mapper_)) {}
    ~IteratorProxy() = default;

    bool is_derived_from(const std::type_info& tinfo) const override { return tinfo == typeid(this_type) || base_type::is_derived_from(tinfo); }

    base_type* copy() const override { return new this_type(*this); }

    IteratorProxy<const T>* const_copy() const { return new IteratorProxy<const T, IT, Mapper>(m_it_, m_mapper_); }

    pointer next() override
    {
        pointer p = nullptr;

        try
        {
            p = m_mapper_(m_it_);
            ++m_it_;
        }
        catch (...)
        {
            p = nullptr;
        }

        return p;
    }

private:
    iterator m_it_;
    mapper_t m_mapper_;
};

template <typename U, typename... V, typename Mapper>
struct IteratorProxy<U, Iterator<V...>, Mapper> : public IteratorProxy<U>
{
public:
    typedef Mapper mapper_t;
    typedef Iterator<V...> iterator;
    typedef IteratorProxy<U, iterator, mapper_t> this_type;
    typedef IteratorProxy<U> base_type;

    using typename base_type::pointer;
    using typename base_type::value_type;

    IteratorProxy(const iterator& it, const mapper_t& mapper) : m_it_(it), m_mapper_(mapper) {}
    IteratorProxy(iterator&& it, mapper_t&& mapper) : m_it_(std::move(it)), m_mapper_(std::move(mapper)) {}
    IteratorProxy(const this_type& other) : m_it_(other.m_it_), m_mapper_(other.m_mapper_) {}
    IteratorProxy(this_type&& other) : m_it_(std::move(other.m_it_)), m_mapper_(std::move(other.m_mapper_)) {}
    ~IteratorProxy() = default;

    bool is_derived_from(const std::type_info& tinfo) const override { return tinfo == typeid(this_type) || base_type::is_derived_from(tinfo); }

    base_type* copy() const override { return new this_type(*this); }

    IteratorProxy<const value_type>* const_copy() const { return new IteratorProxy<const value_type, iterator, mapper_t>(m_it_, m_mapper_); }

    pointer next() override
    {
        pointer p = nullptr;

        // try
        // {
        //     p = m_mapper_(m_it_);
        //     ++m_it_;
        // }
        // catch (...)
        // {
        //     p = nullptr;
        // }

        return p;
    }

private:
    iterator m_it_;
    mapper_t m_mapper_;
};

template <typename T>
class Iterator<T> : public IteratorTraits<T>
{
public:
    typedef IteratorTraits<T> base_type;

    using typename base_type::pointer;
    using typename base_type::reference;
    using typename base_type::value_type;

    template <typename... U>
    friend class Iterator;

    Iterator() : m_proxy_(nullptr), m_current_(nullptr) {}

    Iterator(nullptr_t) = delete;

    Iterator(pointer p) : m_proxy_(nullptr), m_current_(p) {}

    template <typename... Args>
    Iterator(Args&&... args) : m_proxy_(make_iterator_proxy(std::forward<Args>(args)...)), m_current_(m_proxy_->next()) {}

    Iterator(Iterator const& other) : m_proxy_(other.m_proxy_->copy()), m_current_(other.m_current_) {}

    Iterator(Iterator&& other) : m_proxy_(other.m_proxy_.release()), m_current_(other.m_current_) { other.m_current_ = nullptr; }

    ~Iterator() {}

    void swap(Iterator& other)
    {
        std::swap(m_proxy_, other.m_proxy_);

        std::swap(m_current_, other.m_current_);
    }

    Iterator& operator=(Iterator const& other)
    {
        Iterator(other).swap(*this);
        return *this;
    }

    bool operator==(Iterator const& other) const { return m_current_ == other.m_current_; }

    bool operator!=(Iterator const& other) const { return m_current_ != other.m_current_; }

    bool operator==(pointer other) const { return m_current_ == other; }

    bool operator!=(pointer other) const { return m_current_ != other; }

    operator bool() const { return m_current_ != nullptr; }

    pointer next()
    {
        m_current_ = m_proxy_ == nullptr ? nullptr : m_proxy_->next();
        return m_current_;
    }
    Iterator&
    operator++()
    {
        next();
        return *this;
    }

    Iterator operator++(int)
    {
        Iterator res(*this);
        next();
        return res;
    }

    reference operator*() { return *m_current_; }

    pointer operator->() { return m_current_; }

private:
    std::unique_ptr<IteratorProxy<T>> m_proxy_;

    pointer m_current_;

    auto make_iterator_proxy()
    {
        return new IteratorProxy<value_type>();
    }
    auto make_iterator_proxy(value_type* p)
    {
        return new IteratorProxy<value_type>(p);
    }

    template <typename TI>
    auto make_iterator_proxy(const TI& it)
    {
        return new IteratorProxy<value_type, TI>(it);
    }
    template <typename TI, typename Mapper>
    auto make_iterator_proxy(const TI& it, const Mapper& mapper)
    {
        return new IteratorProxy<value_type, TI, Mapper>(it, mapper);
    }

    template <typename TI>
    auto make_iterator_proxy(const TI& it, const std::function<bool(const value_type&)>& filter)
    {
        return new IteratorProxy<value_type, TI, std::function<bool(const value_type&)>>(it, filter);
    }

    template <typename V>
    auto make_iterator_proxy(const Iterator<V>& other, std::enable_if_t<std::is_same_v<value_type, const V>, void*> _ = nullptr)
    {
        return other.m_proxy_->const_copy();
    }
    template <typename V>
    auto make_iterator_proxy(const Iterator<V>& other, std::enable_if_t<std::is_same_v<value_type, V>, void*> _ = nullptr)
    {
        return other.m_proxy_->copy();
    }
};

template <typename... T>
class Iterator : public Iterator<std::tuple<T...>>
{
    typedef Iterator<std::tuple<T...>> base_type;
    using base_type::Iterator;
};

} // namespace sp
#endif //SP_ITERATOR_H_