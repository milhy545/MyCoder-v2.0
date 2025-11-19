package com.mycoder.rocketchat.data.local.dao

import androidx.room.*
import com.mycoder.rocketchat.data.model.Room
import kotlinx.coroutines.flow.Flow

/**
 * Room Data Access Object
 */
@Dao
interface RoomDao {

    @Query("SELECT * FROM rooms WHERE archived = 0 ORDER BY lastMessageAt DESC")
    fun getAllRooms(): Flow<List<Room>>

    @Query("SELECT * FROM rooms WHERE id = :roomId")
    fun getRoomById(roomId: String): Flow<Room?>

    @Query("SELECT * FROM rooms WHERE id = :roomId")
    suspend fun getRoomByIdSync(roomId: String): Room?

    @Query("SELECT * FROM rooms WHERE favorite = 1 AND archived = 0 ORDER BY name ASC")
    fun getFavoriteRooms(): Flow<List<Room>>

    @Query("SELECT * FROM rooms WHERE type = :type AND archived = 0 ORDER BY name ASC")
    fun getRoomsByType(type: Room.RoomType): Flow<List<Room>>

    @Query("SELECT * FROM rooms WHERE unread > 0 AND archived = 0 ORDER BY lastMessageAt DESC")
    fun getUnreadRooms(): Flow<List<Room>>

    @Query("SELECT * FROM rooms WHERE name LIKE '%' || :searchQuery || '%' AND archived = 0")
    fun searchRooms(searchQuery: String): Flow<List<Room>>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertRoom(room: Room)

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertRooms(rooms: List<Room>)

    @Update
    suspend fun updateRoom(room: Room)

    @Delete
    suspend fun deleteRoom(room: Room)

    @Query("UPDATE rooms SET unread = :unread WHERE id = :roomId")
    suspend fun updateUnreadCount(roomId: String, unread: Int)

    @Query("UPDATE rooms SET favorite = :favorite WHERE id = :roomId")
    suspend fun updateFavorite(roomId: String, favorite: Boolean)

    @Query("UPDATE rooms SET open = :open WHERE id = :roomId")
    suspend fun updateOpen(roomId: String, open: Boolean)

    @Query("SELECT COUNT(*) FROM rooms WHERE unread > 0 AND archived = 0")
    fun getTotalUnreadCount(): Flow<Int>
}
