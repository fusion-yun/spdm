#include "DataBlock.h"
#include "../utility/Logger.h"
namespace sp::db
{

DataBlock::DataBlock() {}
DataBlock::~DataBlock() {}
DataBlock::DataBlock(std::shared_ptr<void> data, int element_size, int nd, size_t dimensions) { NOT_IMPLEMENTED; }
DataBlock::DataBlock(DataBlock const&) { NOT_IMPLEMENTED; }
DataBlock::DataBlock(DataBlock&&) { NOT_IMPLEMENTED; }

void DataBlock::swap(DataBlock&) { NOT_IMPLEMENTED; }

} // namespace sp::db