#ifndef SPDB_DATABLOCK_
#define SPDB_DATABLOCK_

#include <memory>
#include <vector>
// #ifdef __cplusplus
// extern "C"
// {
// #endif

// #define SpObject_INTERFACE_HEAD ;

//     typedef struct
//     {
//         SpObject_INTERFACE_HEAD;

//     } SpObjectInterface;

typedef struct
{
    // SpObject_INTERFACE_HEAD;

    char* data;
    unsigned int element_size;
    int dtype;
    int nd;
    unsigned int* dimensions;
    unsigned int* strides;
    int flags;
    char _[];
} DataBlock;

// #ifdef __cplusplus
// }
// #endif

namespace sp::db
{
class DataBlock
{
public:
    DataBlock();

    DataBlock(void* data, int element_size, int nd, const size_t* dimensions);

    DataBlock(int nd, const TDIM* dimensions);

    DataBlock(DataBlock const&);
    DataBlock(DataBlock&&);
    ~DataBlock();

    void swap(DataBlock& other);

    DataBlock& operator=(const DataBlock& other)
    {
        DataBlock(other).swap(*this);
        return *this;
    }
    char* data();
    char const* data() const;
    size_t element_size() const;
    size_t ndims() const;
    size_t const* dims() const;

    template <typename U>
    U* as();
    template <typename U>
    const U* as() const;

    DataBlock slice(const std::tuple<int, int, int>& slice)
    {
        return DataBlock{};
    }
    DataBlock slice(const std::tuple<int, int, int>& slice) const
    {
        return DataBlock{};
    }

private:
    std::shared_ptr<char> m_data_;
    std::vector<size_t> m_dims_;
    size_t m_element_size_ = 1;
};
} // namespace sp::db
#endif // SPDB_DATABLOCK_