#include "Node.h"
#include "Entry.h"
#include "utility/Cursor.h"
#include "utility/Factory.h"
#include "utility/Logger.h"
#include "utility/Path.h"
#include "utility/fancy_print.h"
#include <any>
#include <array>
#include <map>
#include <vector>
namespace sp
{
template <typename... Others>
std::string join_path(const std::string& l, const std::string& r) { return (l == "") ? r : l + "/" + r; }

template <typename... Others>
std::string join_path(const std::string& l, const std::string& r, Others&&... others)
{
    return join_path(join_path(l, r), std::forward<Others>(others)...);
}

Node&& make_node(const std::shared_ptr<Entry>& entry)
{
    NOT_IMPLEMENTED;
    return std::move(Node{});
}

template <typename U>
class CursorProxy<U, std::shared_ptr<Entry>,
                  std::enable_if_t< //
                      std::is_same_v<U, const Node> ||
                      std::is_same_v<U, Node>>> : public CursorProxy<U>
{
public:
    typedef CursorProxy<U, std::shared_ptr<Entry>> this_type;

    typedef CursorProxy<U> base_type;

    using typename base_type::pointer;

    using typename base_type::reference;

    using typename base_type::difference_type;

    CursorProxy(const std::shared_ptr<Entry>& entry) : m_entry_(entry) {}

    ~CursorProxy(){};

    bool done() const override { return get_pointer() == nullptr; }

    bool equal(const base_type* other) const override { return get_pointer() == other->get_pointer(); }

    bool not_equal(const base_type* other) const override { return !equal(other); }

    // difference_type distance(const base_type* other) const override
    // {
    //     NOT_IMPLEMENTED;
    //     return 0;
    // }

    reference get_reference() const override { return std::forward<Node>(make_node(m_entry_)); }

    pointer get_pointer() const override { return std::make_shared<Node>(std::forward<Node>(make_node(m_entry_))); }

    void next() override { m_entry_ = m_entry_->next(); }

private:
    std::shared_ptr<sp::Entry> m_entry_;
};

//--------------------------------------------------------------------------------------------------
// Node

Node::Node(const std::string& backend) : base_type(nullptr, "")
{
    data().template emplace<type_tags::Object>(this, Entry::create(backend).release());
};

Node::Node(Node* parent, const std::string& name) : base_type(parent, name){};

//--------------------------------------------------------------------------------------------------
// Object

template <>
HierarchicalTreeObjectContainer<Node>::HierarchicalTreeObjectContainer(node_type* self, container* container) : m_self_(self), m_container_(container) {}
template <>
HierarchicalTreeObjectContainer<Node>::HierarchicalTreeObjectContainer(this_type&& other) : HierarchicalTreeObjectContainer(other.m_self_, other.m_container_.release()) {}
template <>
HierarchicalTreeObjectContainer<Node>::HierarchicalTreeObjectContainer(const this_type& other) : HierarchicalTreeObjectContainer(other.m_self_, other.m_container_->copy().release()) {}
template <>
HierarchicalTreeObjectContainer<Node>::~HierarchicalTreeObjectContainer() {}

template <>
size_t HierarchicalTreeObjectContainer<Node>::size() const { return m_container_->size(); }

template <>
void HierarchicalTreeObjectContainer<Node>::clear() { m_container_->clear(); }

template <>
int HierarchicalTreeObjectContainer<Node>::count(const std::string& key) const { return m_container_->count(key); }

template <>
HierarchicalTreeObjectContainer<Node>::cursor
HierarchicalTreeObjectContainer<Node>::insert(const std::string& path) { return cursor(m_container_->insert(path)); }

template <>
HierarchicalTreeObjectContainer<Node>::cursor
HierarchicalTreeObjectContainer<Node>::insert(const Path& path) { return cursor(m_container_->insert(path)); }

template <>
void HierarchicalTreeObjectContainer<Node>::erase(const std::string& path) { m_container_->erase(path); }

template <>
void HierarchicalTreeObjectContainer<Node>::erase(const Path& path) { erase(path.str()); }

template <>
HierarchicalTreeObjectContainer<Node>::cursor
HierarchicalTreeObjectContainer<Node>::find(const std::string& path) { return cursor(m_container_->find(path)); }

template <>
HierarchicalTreeObjectContainer<Node>::cursor
HierarchicalTreeObjectContainer<Node>::find(const Path& path) { return cursor(m_container_->find(path)); }

template <>
HierarchicalTreeObjectContainer<Node>::const_cursor
HierarchicalTreeObjectContainer<Node>::find(const std::string& path) const { return const_cursor(m_container_->find(path)); }

template <>
HierarchicalTreeObjectContainer<Node>::const_cursor
HierarchicalTreeObjectContainer<Node>::find(const Path& path) const { return const_cursor(m_container_->find(path)); }

//-----------------------------------------------------------------------------------
// Array

template <>
HierarchicalTreeArrayContainer<Node>::HierarchicalTreeArrayContainer(node_type* self, container* container) : m_self_(self), m_container_(container) {}
template <>
HierarchicalTreeArrayContainer<Node>::HierarchicalTreeArrayContainer(this_type&& other) : HierarchicalTreeArrayContainer(other.m_self_, other.m_container_.release()) {}
template <>
HierarchicalTreeArrayContainer<Node>::HierarchicalTreeArrayContainer(const this_type& other) : HierarchicalTreeArrayContainer(other.m_self_, other.m_container_->copy().release()) {}
template <>
HierarchicalTreeArrayContainer<Node>::~HierarchicalTreeArrayContainer() {}

template <>
size_t HierarchicalTreeArrayContainer<Node>::size() const { return m_container_->size(); }

template <>
void HierarchicalTreeArrayContainer<Node>::resize(std::size_t num) { m_container_->resize(num); }

template <>
void HierarchicalTreeArrayContainer<Node>::clear() { m_container_->clear(); }

template <>
HierarchicalTreeArrayContainer<Node>::cursor
HierarchicalTreeArrayContainer<Node>::push_back() { return cursor(m_container_->push_back()); }

template <>
void HierarchicalTreeArrayContainer<Node>::pop_back() { m_container_->pop_back(); }

template <>
typename node_traits<Node>::reference
HierarchicalTreeArrayContainer<Node>::at(int idx) { return Node(); /*make_node(m_self_, "", m_container_->at(idx)); */ }

template <>
typename node_traits<const Node>::reference
HierarchicalTreeArrayContainer<Node>::at(int idx) const { return std::move(make_node(m_container_->at(idx))); }

// template <>
// class HierarchicalTreeObjectPolicy<Node>
// {
// public:
//     typedef Node node_type;

//     HierarchicalTreeObjectPolicy(const std::string&){};
//     HierarchicalTreeObjectPolicy() = default;
//     HierarchicalTreeObjectPolicy(HierarchicalTreeObjectPolicy&&) = default;
//     HierarchicalTreeObjectPolicy(const HierarchicalTreeObjectPolicy&) = default;
//     ~HierarchicalTreeObjectPolicy() = default;

//     void swap(HierarchicalTreeObjectPolicy& other) { m_data_.swap(other.m_data_); }

//     HierarchicalTreeObjectPolicy& operator=(HierarchicalTreeObjectPolicy const& other)
//     {
//         HierarchicalTreeObjectPolicy(other).swap(*this);
//         return *this;
//     }

//     size_t size() const { return m_data_.size(); }

//     void clear() { m_data_.clear(); }

//     const node_type& at(const std::string& key) const { return m_data_.at(key); };

//     template <typename... Args>
//     node_type& try_emplace(const std::string& key, Args&&... args) { return m_data_.try_emplace(key, std::forward<Args>(args)...).first->second; }

//     node_type& insert(const std::string& path) { return try_emplace(path); }

//     void erase(const std::string& key) { m_data_.erase(key); }

//     // class iterator;

//     template <typename... Args>
//     decltype(auto) find(const std::string& key, Args&&... args) const { return m_data_.find(key); }

//     template <typename... Args>
//     decltype(auto) find(const std::string& key, Args&&... args) { return m_data_.find(key); }

//     decltype(auto) begin() { return m_data_.begin(); }

//     decltype(auto) end() { return m_data_.end(); }

//     decltype(auto) begin() const { return m_data_.cbegin(); }

//     decltype(auto) end() const { return m_data_.cend(); }

//     // template <typename... Args>
//     // const iterator find(const std::string&, Args&&... args) const;

//     // template <typename... Args>
//     // int erase(Args&&... args);

// private:
//     std::map<std::string, node_type> m_data_;
// };

// template <>
// class HierarchicalTreeArrayPolicy<Node>
// {
// public:
//     typedef Node node_type;

//     HierarchicalTreeArrayPolicy() = default;
//     HierarchicalTreeArrayPolicy(HierarchicalTreeArrayPolicy&&) = default;
//     HierarchicalTreeArrayPolicy(const HierarchicalTreeArrayPolicy&) = default;
//     ~HierarchicalTreeArrayPolicy() = default;

//     void swap(HierarchicalTreeArrayPolicy& other) { m_data_.swap(other.m_data_); }

//     HierarchicalTreeArrayPolicy& operator=(HierarchicalTreeArrayPolicy const& other)
//     {
//         HierarchicalTreeArrayPolicy(other).swap(*this);
//         return *this;
//     }

//     size_t size() const { return m_data_.size(); }

//     void resize(size_t s) { m_data_.resize(s); }

//     void clear() { m_data_.clear(); }

//     template <typename... Args>
//     node_type& emplace_back(Args&&... args)
//     {
//         m_data_.emplace_back(std::forward<Args>(args)...);
//         return m_data_.back();
//     }

//     void pop_back() { m_data_.pop_back(); }

//     node_type& at(int idx) { return m_data_.at(idx); }

//     const node_type& at(int idx) const { return m_data_.at(idx); }

//     decltype(auto) begin() { return m_data_.begin(); }

//     decltype(auto) end() { return m_data_.end(); }

//     decltype(auto) begin() const { return m_data_.cbegin(); }

//     decltype(auto) end() const { return m_data_.cend(); }

// private:
//     std::vector<node_type> m_data_;
// };

// // as Tree
// // as container

// Node Node::parent() const
// {
//     auto pos = m_path_.rfind("/");
//     if (pos == std::string::npos)
//     {
//         return Node(m_entry_->parent());
//     }
//     else
//     {
//         return Node(m_entry_->parent(), m_path_.substr(0, pos));
//     }
// }

// size_t Node::size() const { return self()->size(); }

// Node::cursor Node::first_child() const { return cursor{self()->first_child()}; }

// Node::cursor Node::next() const { return cursor{self()->next()}; }
// // as array

// Node Node::push_back() { return Node{self()->push_back()}; }

// Node Node::pop_back() { return Node{self()->pop_back()}; }

// Node Node::operator[](int idx) { return idx < 0 ? Node{push_back()} : Node{self()->item(idx)}; }

// Node Node::operator[](int idx) const { return Node{self()->item(idx)}; }

// // as map
// // @note : map is unordered
// bool Node::has_a(const std::string& name) const { return m_entry_->find(join_path(m_path_, name)) != nullptr; }

// Node Node::find(const std::string& name) const { return Node(m_entry_->find(join_path(m_path_, name))); }

// Node Node::operator[](const std::string& name) { return Node(m_entry_, join_path(m_path_, name)); }

// Node Node::insert(const std::string& name) { return Node(m_entry_->insert(join_path(m_path_, name))); }

// void Node::remove(const std::string& name) { m_entry_->remove(join_path(m_path_, name)); }

// //-------------------------------------------------------------------
// // level 2
// size_t Node::depth() const { return m_entry_ == nullptr ? 0 : parent().depth() + 1; }

// size_t Node::height() const
// {
//     NOT_IMPLEMENTED;
//     return 0;
// }

// Node::cursor Node::slibings() const { return Node::cursor{}; }

// Node::cursor Node::ancestor() const
// {
//     NOT_IMPLEMENTED;
//     return Node::cursor{};
// }

// Node::cursor Node::descendants() const
// {
//     NOT_IMPLEMENTED;
//     return Node::cursor{};
// }

// Node::cursor Node::leaves() const
// {
//     NOT_IMPLEMENTED;
//     return Node::cursor{};
// }

// Node::cursor Node::shortest_path(Node const& target) const
// {
//     NOT_IMPLEMENTED;
//     return Node::cursor{};
// }

// ptrdiff_t Node::distance(const this_type& target) const
// {
//     NOT_IMPLEMENTED;
//     return 0;
// }

// Node load(const std::string& uri) { NOT_IMPLEMENTED; }

// void save(const Node&, const std::string& uri) { NOT_IMPLEMENTED; }

// Node load(const std::istream&, const std::string& format) { NOT_IMPLEMENTED; }

// void save(const Node&, const std::ostream&, const std::string& format) { NOT_IMPLEMENTED; }

// std::ostream& fancy_print(std::ostream& os, const Node& entry, int indent = 0, int tab = 4)
// {

//     if (entry.type() == Entry::NodeType::Element)
//     {
//         os << to_string(entry.get_element());
//     }
//     else if (entry.type() == Entry::NodeType::Array)
//     {
//         os << "[";
//         for (auto it = entry.first_child(); !it.is_null(); ++it)
//         {
//             os << std::endl
//                << std::setw(indent * tab) << " ";
//             fancy_print(os, it->value(), indent + 1, tab);
//             os << ",";
//         }
//         os << std::endl
//            << std::setw(indent * tab)
//            << "]";
//     }
//     else if (entry.type() == Entry::NodeType::Object)
//     {
//         os << "{";
//         for (auto it = entry.first_child(); !it.is_null(); ++it)
//         {
//             os << std::endl
//                << std::setw(indent * tab) << " "
//                << "\"" << it->name() << "\" : ";
//             fancy_print(os, it->value(), indent + 1, tab);
//             os << ",";
//         }
//         os << std::endl
//            << std::setw(indent * tab)
//            << "}";
//     }
//     return os;
// }

// std::ostream& operator<<(std::ostream& os, Node const& entry) { return fancy_print(os, entry, 0); }

// Node::cursor::cursor() : m_entry_(nullptr) {}

// Node::cursor::cursor(Entry* p) : m_entry_(p == nullptr ? nullptr : p->shared_from_this()) {}

// Node::cursor::cursor(const std::shared_ptr<Entry>& p) : m_entry_(p) {}

// Node::cursor::cursor(const cursor& other) : m_entry_(other.m_entry_->copy()) {}

// Node::cursor::cursor(cursor&& other) : m_entry_(other.m_entry_) { other.m_entry_.reset(); }

// bool Node::cursor::operator==(cursor const& other) const { return m_entry_ == other.m_entry_ || (m_entry_ != nullptr && m_entry_->same_as(other.m_entry_.get())); }

// bool Node::cursor::operator!=(cursor const& other) const { return !(operator==(other)); }

// Node Node::cursor::operator*() { return Node(m_entry_); }

// bool Node::cursor::is_null() const { return m_entry_ == nullptr || m_entry_->type() == Entry::Null; }

// std::unique_ptr<Node> Node::cursor::operator->() { return std::make_unique<Node>(m_entry_); }

// Node::cursor& Node::cursor::operator++()
// {
//     m_entry_ = m_entry_->next();
//     return *this;
// }

// Node::cursor Node::cursor::operator++(int)
// {
//     Node::cursor res(*this);
//     m_entry_ = m_entry_->next();
//     return std::move(res);
// }

} // namespace sp